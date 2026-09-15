"""Login security regressions using dummy identities and isolated provider boundaries."""

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException

from app.config import config
from app.middleware.auth_middleware import _validate_token_security, _verify_via_supabase_api, decode_supabase_token
from app.services.auth_service import AuthService
from app.services.google_auth_service import GoogleAuthService
from app.services.otp_service import OTPService
from app.services.token_service import TokenService
from app.utils.auth_utils import decode_token

USER_ID = "00000000-0000-4000-a000-000000000123"


@pytest.fixture
def service():
    return AuthService(MagicMock(), MagicMock())


@pytest.mark.asyncio
async def test_refresh_rejects_password_revocation_and_unavailable_database(service):
    token = service.create_refresh_token(USER_ID, "127.0.0.1", "test-agent")
    ts = AsyncMock()
    with (
        patch.object(service, "is_token_revoked", new=AsyncMock(return_value=False)),
        patch("app.services.auth.token_mixin.get_token_service", new=AsyncMock(return_value=ts)),
    ):
        ts.is_user_invalidated.return_value = True
        assert await service.verify_refresh_token(token) is None
        ts.is_user_invalidated.side_effect = RuntimeError("database unavailable")
        assert await service.verify_refresh_token(token) is None
        ts.is_user_invalidated.side_effect = None
        ts.is_user_invalidated.return_value = False
        assert await service.verify_refresh_token(token, "127.0.0.1", "test-agent")
        assert await service.verify_refresh_token(token, "127.0.0.2", "test-agent") is None


@pytest.mark.parametrize("missing", ["sub", "user_id", "exp", "iat", "jti", "type", "iss", "aud"])
@pytest.mark.asyncio
async def test_refresh_requires_security_claims(service, missing):
    claims = jwt.decode(service.create_refresh_token(USER_ID), options={"verify_signature": False})
    claims.pop(missing)
    token = jwt.encode(claims, str(config.JWT_REFRESH_SECRET), algorithm="HS256")
    assert await service.verify_refresh_token(token) is None


def test_refresh_cannot_be_used_as_access_even_with_same_signing_key(service):
    with patch.object(config, "JWT_REFRESH_SECRET", config.JWT_SECRET):
        token = service.create_refresh_token(USER_ID)
    assert service.verify_access_token(token) is None
    with pytest.raises(ValueError):
        decode_token(token)


def test_access_token_rejects_wrong_issuer_audience_and_missing_type(service):
    token = service.create_access_token(USER_ID)
    claims = jwt.decode(token, options={"verify_signature": False})
    assert service.verify_access_token(token) == USER_ID
    for change in ({"iss": "other"}, {"aud": "other"}, {"type": None}):
        changed = claims | change
        if "type" in change and change["type"] is None:
            changed.pop("type")
        invalid = jwt.encode(changed, config.JWT_SECRET, algorithm="HS256")
        assert service.verify_access_token(invalid) is None


@pytest.mark.asyncio
async def test_refresh_consumption_requires_durable_unique_insert():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    first = MagicMock()
    first.fetchone.return_value = ("jti",)
    duplicate = MagicMock()
    duplicate.fetchone.return_value = None
    db.execute.side_effect = [first, duplicate, RuntimeError("database unavailable")]
    ts = TokenService(db=db)
    expiry = datetime.now(UTC) + timedelta(hours=1)
    assert await ts.consume_refresh_token("jti", USER_ID, expiry) is True
    assert await ts.consume_refresh_token("jti", USER_ID, expiry) is False
    assert await ts.consume_refresh_token("jti2", USER_ID, expiry) is False
    assert "ON CONFLICT (token_jti) DO NOTHING RETURNING" in str(db.execute.call_args_list[0].args[0])
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_global_revocation_binds_datetime_for_postgres_timestamp():
    db = MagicMock()
    db.commit = AsyncMock()

    async def require_datetime(_query, params):
        assert isinstance(params["now"], datetime)
        assert params["now"].tzinfo is UTC

    db.execute = AsyncMock(side_effect=require_datetime)
    ts = TokenService(db=db)

    assert await ts.blacklist_all_user_tokens(USER_ID, reason="password_change") == 1
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_provider_fallback_preserves_original_issue_time():
    now = int(datetime.now(UTC).timestamp())
    token = jwt.encode(
        {"sub": USER_ID, "iat": now - 300, "exp": now + 300}, "dummy-provider-secret-for-test-only", algorithm="HS256"
    )
    client = MagicMock()
    client.auth.get_user = AsyncMock(
        return_value=SimpleNamespace(
            user=SimpleNamespace(id=USER_ID, email="test@example.com", user_metadata={}, app_metadata={})
        )
    )
    payload = await _verify_via_supabase_api(token, client)
    assert payload is not None
    assert payload["iat"] == now - 300
    ts = AsyncMock()
    ts.is_user_invalidated.return_value = True
    with (
        patch("app.middleware.auth_middleware.get_token_service", new=AsyncMock(return_value=ts)),
        pytest.raises(HTTPException, match="Session invalidated"),
    ):
        await _validate_token_security(payload)


@pytest.mark.asyncio
async def test_recovery_session_cannot_authorize_application_requests():
    now = int(datetime.now(UTC).timestamp())
    payload = {
        "sub": USER_ID,
        "iat": now,
        "exp": now + 300,
        "amr": [{"method": "recovery", "timestamp": now}],
    }
    with pytest.raises(HTTPException, match="Recovery session"):
        await _validate_token_security(payload)


@pytest.mark.parametrize("algorithm", ["RS256", "ES256"])
@pytest.mark.asyncio
async def test_provider_signature_issuer_audience_and_expiration(algorithm):
    key = (
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if algorithm == "RS256"
        else ec.generate_private_key(ec.SECP256R1())
    )
    if algorithm == "RS256":
        assert isinstance(key, rsa.RSAPrivateKey)
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    else:
        assert isinstance(key, ec.EllipticCurvePrivateKey)
        jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(key.public_key()))
    jwk["kid"] = "test-key"
    issuer = "https://testproject.supabase.co/auth/v1"
    now = int(datetime.now(UTC).timestamp())
    claims = {"sub": USER_ID, "iat": now, "exp": now + 300, "aud": "authenticated", "iss": issuer}
    with (
        patch("app.middleware.auth_middleware.get_jwks", new=AsyncMock(return_value={"keys": [jwk]})),
        patch.object(config, "SUPABASE_URL", "https://testproject.supabase.co"),
    ):
        token = jwt.encode(claims, key, algorithm=algorithm, headers={"kid": "test-key"})
        assert (await decode_supabase_token(token))["sub"] == USER_ID
        for change in ({"iss": "https://other.example"}, {"aud": "anon"}, {"exp": now - 1}):
            invalid = jwt.encode(claims | change, key, algorithm=algorithm, headers={"kid": "test-key"})
            with pytest.raises(HTTPException):
                await decode_supabase_token(invalid)


@pytest.mark.asyncio
async def test_otp_cannot_succeed_when_compare_and_swap_loses():
    service = OTPService(MagicMock())
    record = {
        "id": "record",
        "otp_hash": service._hash_otp("123456"),
        "attempts": 0,
        "max_attempts": 5,
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
    }
    with (
        patch.object(service, "_is_email_locked_out", new=AsyncMock(return_value=False)),
        patch.object(service, "_fetch_pending_verification", new=AsyncMock(return_value=record)),
        patch.object(service, "_claim_attempt", new=AsyncMock(side_effect=[True, False])),
        patch.object(service, "_clear_email_lockout", new=AsyncMock()),
    ):
        outcomes = await asyncio.gather(
            service.verify_otp("TEST@example.com", "123456"), service.verify_otp("test@example.com", "123456")
        )
    assert sum(result["success"] for result in outcomes) == 1


@pytest.mark.asyncio
async def test_otp_fails_closed_when_lockout_lookup_fails():
    service = OTPService(MagicMock())
    with (
        patch.object(service, "_run_redis_otp_op", new=AsyncMock(return_value=(False, None))),
        patch.object(
            service, "_fetch_pending_verification", new=AsyncMock(side_effect=RuntimeError("database unavailable"))
        ),
    ):
        assert await service._is_email_locked_out("test@example.com") is True


@pytest.mark.asyncio
async def test_unverified_identity_comes_from_auth_not_public_profile(service):
    identity = {"id": USER_ID, "email": "test@example.com", "email_confirmed_at": None}
    service._supabase_admin.rpc.return_value.execute = AsyncMock(return_value=SimpleNamespace(data=[identity]))
    service._supabase_admin.auth.admin.update_user_by_id = AsyncMock()
    assert await service.confirm_user_email("TEST@example.com") is True
    service._supabase_admin.rpc.assert_called_once_with("get_auth_user_by_email", {"p_email": "test@example.com"})
    service._supabase_admin.auth.admin.update_user_by_id.assert_awaited_once_with(USER_ID, {"email_confirm": True})


@pytest.mark.asyncio
async def test_google_email_linking_requires_provider_authority(service):
    with patch.object(service, "_find_user_supabase", new=AsyncMock(return_value=USER_ID)) as lookup:
        await service._find_or_create_google_user({"email": "thirdparty@example.com"}, "google-id")
        lookup.assert_awaited_once_with("google-id", None)


def test_google_rejects_unverified_email_and_marks_authority():
    service = GoogleAuthService()
    service.google_client_id = "dummy-client"
    claims = {"iss": "https://accounts.google.com", "sub": "g1", "email": "test@example.com", "email_verified": False}
    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=claims):
        with pytest.raises(ValueError, match="not verified"):
            service.verify_google_token("token")
        claims["email_verified"] = True
        assert service.verify_google_token("token")["email_authoritative"] is False
        claims["hd"] = "example.com"
        assert service.verify_google_token("token")["email_authoritative"] is True


def test_otp_hash_is_keyed_and_domain_separated():
    service = OTPService(MagicMock())
    digest = service._hash_otp("123456")
    assert digest != hashlib.sha256(b"123456").hexdigest()
    with patch.object(config, "JWT_SECRET", "different-secret"):
        assert service._hash_otp("123456") != digest


@pytest.mark.asyncio
async def test_reset_requires_recent_recovery_and_consumes_session(service):
    now = int(datetime.now(UTC).timestamp())
    claims = {
        "sub": USER_ID,
        "iat": now,
        "exp": now + 300,
        "session_id": "session-test",
        "amr": [{"method": "password", "timestamp": now}],
    }
    service._supabase.auth.get_user = AsyncMock(
        return_value=SimpleNamespace(user=SimpleNamespace(id=USER_ID, email="test@example.com"))
    )
    service._supabase_admin.auth.admin.update_user_by_id = AsyncMock()
    service._supabase_admin.table.return_value.update.return_value.eq.return_value.execute = AsyncMock()
    ts = AsyncMock()
    ts.is_user_invalidated.return_value = False
    ts.blacklist_all_user_tokens.return_value = 1
    ts.consume_refresh_token.side_effect = [True, False]
    with (
        patch(
            "app.services.auth.password_mixin.password_service.validate_new_password",
            new=AsyncMock(return_value=(True, None)),
        ),
        patch("app.services.auth.password_mixin.get_token_service", new=AsyncMock(return_value=ts)),
        patch("app.services.auth.password_mixin.email_service.send_password_changed_email"),
    ):
        ordinary = jwt.encode(claims, "dummy-provider-secret-for-test-only", algorithm="HS256")
        assert await service.reset_password(ordinary, "new-safe-passphrase") is False
        service._supabase_admin.auth.admin.update_user_by_id.assert_not_awaited()
        claims["amr"] = [{"method": "recovery", "timestamp": now}]
        recovery = jwt.encode(claims, "dummy-provider-secret-for-test-only", algorithm="HS256")
        assert await service.reset_password(recovery, "new-safe-passphrase") is True
        assert await service.reset_password(recovery, "another-passphrase") is False
        service._supabase_admin.auth.admin.update_user_by_id.assert_awaited_once()
