from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.auth_service import AuthService
from user_models.user import User


class TestAuthServiceExtended:
    @pytest.fixture
    def mock_supabase(self):
        return MagicMock()

    @pytest.fixture
    def auth_service(self, mock_supabase):
        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase):
            with patch.dict(
                "os.environ",
                {"GOOGLE_CLIENT_ID": "test_id", "GOOGLE_CLIENT_SECRET": "test_secret", "JWT_SECRET": "test_jwt_secret"},
            ):
                service = AuthService(mock_supabase)
                service.google_client_id = "test_id"
                service.google_client_secret = "test_secret"
                service.jwt_secret = "test_jwt_secret"
                service.supabase_admin = mock_supabase
                return service

    def test_verify_google_token_success(self, auth_service):
        with patch("google.oauth2.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "accounts.google.com",
                "sub": "google123",
                "email": "test@gmail.com",
                "name": "Tester",
                "picture": "http://pic",
            }

            user_info = auth_service.verify_google_token("valid_token")
            assert user_info["google_id"] == "google123"
            assert user_info["email"] == "test@gmail.com"

    def test_verify_google_token_wrong_issuer(self, auth_service):
        with patch("google.oauth2.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "bad_issuer",
            }
            with pytest.raises(ValueError, match="Invalid token"):
                auth_service.verify_google_token("token")

    def test_create_and_verify_access_token(self, auth_service):
        token = auth_service.create_access_token("user123", {"email": "t@t.com"})
        assert token is not None

        user_id = auth_service.verify_access_token(token)
        assert user_id == "user123"

    @pytest.mark.asyncio
    async def test_create_and_verify_refresh_token(self, auth_service, mock_supabase):
        # Mock TokenService
        mock_token_service = AsyncMock()
        mock_token_service.is_blacklisted.return_value = False

        with patch("services.auth_service.get_token_service", new_callable=AsyncMock) as mock_get_service:
            mock_get_service.return_value = mock_token_service

            # Create token with fingerprint
            token = auth_service.create_refresh_token("user123", ip="1.2.3.4", user_agent="Mozilla")

            assert token is not None

            # Verify with matching fingerprint - await added
            payload = await auth_service.verify_refresh_token(token, ip="1.2.3.4", user_agent="Mozilla")
            assert payload is not None
            assert payload["user_id"] == "user123"

            # Verify with mismatching fingerprint - await added
            payload_mismatch = await auth_service.verify_refresh_token(token, ip="9.9.9.9", user_agent="Bot")
            assert payload_mismatch is None

    @pytest.mark.asyncio
    async def test_revocation_logic(self, auth_service):
        # Mock TokenService
        mock_token_service = AsyncMock()
        mock_token_service.is_blacklisted.side_effect = lambda jti: jti == "jti_123"
        mock_token_service.blacklist_token.return_value = True

        with patch("services.auth_service.get_token_service", new_callable=AsyncMock) as mock_get_service:
            mock_get_service.return_value = mock_token_service

            # Test is_token_revoked
            assert await auth_service.is_token_revoked("jti_123") is True
            assert await auth_service.is_token_revoked("jti_clean") is False

            # Test revoke_token
            success = await auth_service.revoke_token("jti_new", "u1", datetime(2025, 1, 1))
            assert success is True

            mock_token_service.blacklist_token.assert_called_once()

    def test_verify_access_token_invalid(self, auth_service):
        assert auth_service.verify_access_token("bad_token") is None

    def test_authenticate_user_success(self, auth_service):
        hashed = auth_service.hash_password("pass123")
        with patch.object(auth_service, "get_user_by_email") as mock_get:
            mock_get.return_value = {"id": "u1", "password_hash": hashed, "name": "U"}

            user = auth_service.authenticate_user("u@example.com", "pass123")
            assert user is not None
            assert user["id"] == "u1"

    def test_authenticate_user_fail_password(self, auth_service):
        hashed = auth_service.hash_password("pass123")
        with patch.object(auth_service, "get_user_by_email") as mock_get:
            mock_get.return_value = {"id": "u1", "password_hash": hashed}

            user = auth_service.authenticate_user("u@example.com", "WRONG")
            assert user is None

    def test_create_user_with_password(self, auth_service, mock_supabase):
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new1", "email": "n@n.com"}]
        )

        user = auth_service.create_user_with_password("n@n.com", "pass", "N")
        assert user["id"] == "new1"
        mock_supabase.table.assert_called_with("users")

    def test_create_password_reset_token_success(self, auth_service, mock_supabase):
        with patch.object(auth_service, "get_user_by_email", return_value={"id": "u1"}):
            token = auth_service.create_password_reset_token("t@t.com")
            assert token is not None
            mock_supabase.table.return_value.insert.assert_called()

    def test_reset_password_success(self, auth_service, mock_supabase):
        # Mock valid token record
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.gt.return_value.execute.return_value = MagicMock(
            data=[{"id": "r1", "user_id": "u1"}]
        )

        # Mock update success
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        success = auth_service.reset_password("valid_token", "newpass")
        assert success is True

    @pytest.mark.asyncio
    async def test_exchange_google_code_success(self, auth_service, mock_supabase):
        # Mock HTTPX response for token exchange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "g_access", "id_token": "g_id_token"}

        # Mock ID Token verification
        with patch("google.oauth2.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "accounts.google.com",
                "sub": "goog_sub",
                "email": "t@gmail.com",
                "name": "Tester",
                "picture": "pic",
            }

            # Mock DB logic: find existing user fail, upsert success
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[]
            )

            # Mock create_or_get_user (we can patch the internal call or let it run mocked DB)
            # Let's let it run but mock DB upsert

            # The code calls:
            # self.supabase_admin.table("users").upsert(...)
            mock_upsert_res = MagicMock()
            mock_upsert_res.data = [
                {
                    "id": "new_uid",
                    "email": "t@gmail.com",
                    "name": "Tester",
                    "picture": "pic",
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ]
            mock_supabase.table.return_value.upsert.return_value.execute.return_value = mock_upsert_res

            # Also create_or_get_user calls upsert.
            # exchange_google_code calls create_or_get_user.

            # We need to mock AsyncClient
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                login_response = await auth_service.exchange_google_code("code", "ver", "redir")

                assert login_response.access_token is not None
                assert login_response.user.email == "t@gmail.com"

    @pytest.mark.asyncio
    async def test_exchange_google_code_http_error(self, auth_service):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(ValueError, match="Token exchange failed"):
                await auth_service.exchange_google_code("code", "ver", "redir")
