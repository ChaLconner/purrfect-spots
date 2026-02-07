# nosec python:S2068, python:S5332 - Hardcoded secrets/URLs in this file are intentional test fixtures
# These are not real credentials/URLs; they are used only for unit testing authentication

import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from middleware.auth_middleware import (
    _get_user_from_payload,
    _verify_and_decode_token,
    decode_custom_token,
    decode_supabase_token,
    get_current_user,
    get_jwks,
)
from user_models.user import User

# --- Fixtures ---


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"SUPABASE_URL": "https://testproject.supabase.co", "JWT_SECRET": "supersecretkey"}):
        yield


@pytest.fixture
def mock_jwks_response():
    return {"keys": [{"kid": "key1", "kty": "RSA", "n": "abc", "e": "AQAB"}]}


# --- Tests for get_jwks ---


@pytest.mark.asyncio
async def test_get_jwks_success(mock_env, mock_jwks_response):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jwks_response
        mock_get.return_value = mock_response

        # Reset cache globals
        with (
            patch("middleware.auth_middleware._jwks_cache", None),
            patch("middleware.auth_middleware._jwks_last_update", 0),
        ):
            jwks = await get_jwks()
            assert jwks == mock_jwks_response
            mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_jwks_cached(mock_env, mock_jwks_response):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Pre-set cache
        with (
            patch("middleware.auth_middleware._jwks_cache", mock_jwks_response),
            patch("middleware.auth_middleware._jwks_last_update", time.time()),
        ):
            jwks = await get_jwks()
            assert jwks == mock_jwks_response
            mock_get.assert_not_called()


@pytest.mark.asyncio
async def test_get_jwks_no_url():
    with patch.dict(os.environ, {}, clear=True):
        jwks = await get_jwks()
        assert jwks is None


# --- Tests for decode_supabase_token ---


@pytest.mark.asyncio
async def test_decode_supabase_token_success(mock_env, mock_jwks_response):
    with patch("middleware.auth_middleware.get_jwks", new_callable=AsyncMock) as mock_get_jwks:
        mock_get_jwks.return_value = mock_jwks_response

        with (
            patch("jwt.get_unverified_header") as mock_header,
            patch("jwt.algorithms.RSAAlgorithm.from_jwk") as mock_algo,
            patch("jwt.decode") as mock_decode,
        ):
            mock_header.return_value = {"kid": "key1"}
            mock_algo.return_value = "public_key_obj"
            mock_decode.return_value = {"sub": "user123", "aud": "authenticated"}

            payload = await decode_supabase_token("valid_token")
            assert payload["sub"] == "user123"


@pytest.mark.asyncio
async def test_decode_supabase_token_no_jwks(mock_env):
    with patch("middleware.auth_middleware.get_jwks", new_callable=AsyncMock) as mock_get_jwks:
        mock_get_jwks.return_value = None

        with pytest.raises(HTTPException) as exc:
            await decode_supabase_token("token")
        assert exc.value.status_code == 401
        assert "Invalid Supabase token" in exc.value.detail


@pytest.mark.asyncio
async def test_decode_supabase_token_missing_kid(mock_env, mock_jwks_response):
    with patch("middleware.auth_middleware.get_jwks", new_callable=AsyncMock) as mock_get_jwks:
        mock_get_jwks.return_value = mock_jwks_response
        with patch("jwt.get_unverified_header", return_value={}):
            with pytest.raises(HTTPException) as exc:
                await decode_supabase_token("token")
            assert exc.value.status_code == 401
            assert "missing 'kid'" in exc.value.detail


# --- Tests for decode_custom_token ---


def test_decode_custom_token_success(mock_env):
    with patch("middleware.auth_middleware.config.JWT_SECRET", "supersecretkey"):
        with patch("jwt.decode", return_value={"sub": "user123"}) as mock_decode:
            payload = decode_custom_token("token")
            assert payload["sub"] == "user123"
            mock_decode.assert_called()
            args = mock_decode.call_args
            assert args[0][0] == "token"
            assert args[0][1] == "supersecretkey"


def test_decode_custom_token_no_secret():
    with patch("middleware.auth_middleware.config.JWT_SECRET", None):
        with pytest.raises(HTTPException) as exc:
            decode_custom_token("token")
        assert exc.value.status_code == 500
        assert "JWT_SECRET not set" in exc.value.detail


def test_decode_custom_token_expired(mock_env):
    from jwt import ExpiredSignatureError

    with patch("middleware.auth_middleware.config.JWT_SECRET", "supersecretkey"):
        with patch("jwt.decode", side_effect=ExpiredSignatureError):
            with pytest.raises(HTTPException) as exc:
                decode_custom_token("token")
            assert exc.value.status_code == 401
            assert "Token expired" in exc.value.detail


# --- Tests for _get_user_from_payload ---


def test_get_user_from_payload_supabase_no_db(mock_env):
    payload = {
        "sub": "user123",
        "email": "test@example.com",
        "user_metadata": {"full_name": "Test User", "avatar_url": "http://img.com"},
    }

    mock_deps = MagicMock()
    mock_deps.get_supabase_admin_client.side_effect = Exception("DB error")

    with patch.dict(sys.modules, {"dependencies": mock_deps}):
        user = _get_user_from_payload(payload, "supabase")
        assert user.id == "user123"
        assert user.name == "Test User"
        assert user.picture == "http://img.com"


def test_get_user_from_payload_custom(mock_env):
    payload = {
        "sub": "user123",
        "name": "Custom User",
        "email": "custom@example.com",
        "picture": "http://custom.com",
        "iat": 123456,
    }
    mock_deps = MagicMock()
    mock_deps.get_supabase_admin_client.side_effect = Exception("DB error")

    with patch.dict(sys.modules, {"dependencies": mock_deps}):
        user = _get_user_from_payload(payload, "custom")
        assert user.id == "user123"
        assert user.name == "Custom User"


def test_get_user_from_payload_db_success(mock_env):
    payload = {"sub": "user123"}

    mock_sb = MagicMock()
    # Mock chain: .table().select().eq().single().execute().data
    mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "user123",
        "email": "db@example.com",
        "name": "DB User",
        "picture": "db.jpg",
        "bio": "Hello",
        "created_at": None,
    }

    with patch("middleware.auth_middleware.get_supabase_admin_client", return_value=mock_sb):
        user = _get_user_from_payload(payload, "supabase")
        assert user.email == "db@example.com"
        assert user.bio == "Hello"


# --- Tests for verify_and_decode_token ---


@pytest.mark.asyncio
async def test_verify_and_decode_token_supabase_ok(mock_env):
    with patch("middleware.auth_middleware.decode_supabase_token", new_callable=AsyncMock) as mock_supa:
        mock_supa.return_value = {"sub": "123"}
        payload, source = await _verify_and_decode_token("token")
        assert payload == {"sub": "123"}
        assert source == "supabase"


@pytest.mark.asyncio
async def test_verify_and_decode_token_fallback_custom(mock_env):
    with (
        patch("middleware.auth_middleware.decode_supabase_token", side_effect=ValueError),
        patch("middleware.auth_middleware.decode_custom_token") as mock_cust,
    ):
        mock_cust.return_value = {"sub": "456"}
        payload, source = await _verify_and_decode_token("token")
        assert payload == {"sub": "456"}
        assert source == "custom"


@pytest.mark.asyncio
async def test_verify_and_decode_token_all_fail(mock_env):
    with (
        patch("middleware.auth_middleware.decode_supabase_token", side_effect=ValueError),
        patch("middleware.auth_middleware.decode_custom_token", side_effect=Exception),
    ):
        with pytest.raises(HTTPException) as exc:
            await _verify_and_decode_token("token")
        assert exc.value.status_code == 401


# --- Tests for public wrappers ---


@pytest.mark.asyncio
async def test_get_current_user_from_request_success(mock_env):
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "Bearer valid_token"

    with (
        patch("middleware.auth_middleware._verify_and_decode_token", new_callable=AsyncMock) as mock_verify,
        patch("middleware.auth_middleware._get_user_from_payload") as mock_get_user,
    ):
        mock_verify.return_value = ({"sub": "123"}, "supabase")
        mock_get_user.return_value = User(id="123", email="t@t.com", name="T", picture="p", bio="b", created_at=None)

        user = await get_current_user(mock_request)
        assert user.id == "123"


@pytest.mark.asyncio
async def test_get_current_user_from_request_no_token(mock_env):
    mock_request = MagicMock()
    mock_request.headers.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await get_current_user(mock_request)
    assert exc.value.status_code == 401
