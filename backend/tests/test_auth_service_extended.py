# pylint: disable=redefined-outer-name
# nosec python:S2068, python:S1313 - Hardcoded secrets/IPs are intentional test fixtures

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.auth_service import AuthService


@pytest.mark.asyncio
class TestAuthServiceExtended:
    @pytest.fixture
    def mock_supabase(self):
        # Mock Supabase client
        mock = MagicMock()
        mock.auth = MagicMock()
        # Ensure exchange_google_code -> upsert/select works

        # Chainable mock for table().select().eq().execute()
        chain_mock = MagicMock()
        chain_mock.select.return_value = chain_mock
        chain_mock.eq.return_value = chain_mock
        chain_mock.maybe_single.return_value = chain_mock
        chain_mock.single.return_value = chain_mock
        chain_mock.update.return_value = chain_mock
        chain_mock.upsert.return_value = chain_mock
        chain_mock.execute = AsyncMock(return_value=MagicMock(data=[]))

        mock.table = MagicMock(return_value=chain_mock)
        return mock

    @pytest.fixture
    def mock_user_service_instance(self):
        mock = MagicMock()
        mock.create_or_get_user = AsyncMock()
        mock.get_user_by_id = AsyncMock()
        mock.update_user_profile = AsyncMock()
        mock.authenticate_user = AsyncMock()
        mock.create_unverified_user = AsyncMock()
        mock.get_user_by_email = AsyncMock()
        mock.get_user_by_username = AsyncMock()
        return mock

    @pytest.fixture
    def auth_service(self, mock_supabase, mock_user_service_instance):
        with patch("services.auth_service.UserService", return_value=mock_user_service_instance):
            with patch(
                "services.auth_service.get_async_supabase_admin_client", new=AsyncMock(return_value=mock_supabase)
            ):
                # Patch config
                with patch.dict(
                    "os.environ",
                    {
                        "GOOGLE_CLIENT_ID": "test_id",
                        "GOOGLE_CLIENT_SECRET": "test_secret",
                        "JWT_SECRET": "test_jwt_secret_must_be_at_least_32_characters_long",
                    },
                ):
                    service = AuthService(mock_supabase, mock_supabase)  # Pass admin too
                    service.google_client_id = "test_id"
                    service.google_client_secret = "test_secret"
                    service.jwt_secret = "test_jwt_secret_must_be_at_least_32_characters_long"
                    service.jwt_algorithm = "HS256"

                    yield service

    def test_verify_google_token_success(self, auth_service):
        with patch("google.oauth2.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "accounts.google.com",
                "sub": "google123",
                "email": "test@gmail.com",
                "name": "Tester",
                "picture": "http://pic",
                "aud": "test_id",
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
        token = auth_service.create_access_token("00000000-0000-4000-a000-000000000123", {"email": "t@t.com"})
        assert token is not None

        user_id = auth_service.verify_access_token(token)
        assert user_id == "00000000-0000-4000-a000-000000000123"

    @pytest.mark.asyncio
    async def test_create_and_verify_refresh_token(self, auth_service):
        # Mock is_token_revoked
        auth_service.is_token_revoked = AsyncMock(return_value=False)

        # Create token with fingerprint
        token = auth_service.create_refresh_token(
            "00000000-0000-4000-a000-000000000123", ip="1.2.3.4", user_agent="Mozilla"
        )

        assert token is not None

        # Verify with matching fingerprint
        payload = await auth_service.verify_refresh_token(token, ip="1.2.3.4", user_agent="Mozilla")
        assert payload is not None
        assert payload["user_id"] == "00000000-0000-4000-a000-000000000123"

        # Verify with mismatching fingerprint
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

    @pytest.mark.asyncio
    async def test_exchange_google_code_success(self, auth_service, mock_supabase, mock_user_service_instance):
        # Mocks
        with patch(
            "services.google_auth_service.google_auth_service.exchange_google_code", new_callable=AsyncMock
        ) as mock_exchange:
            mock_exchange.return_value = {
                "user_info": {"google_id": "goog_sub", "email": "t@gmail.com", "name": "Tester", "picture": "pic"}
            }

            # user_service.create_or_get_user mock
            fake_user = MagicMock()
            fake_user.id = "u1"
            fake_user.role = "user"
            fake_user.permissions = []
            fake_user.email = "t@gmail.com"
            fake_user.name = "Tester"
            fake_user.picture = "pic"
            fake_user.bio = None
            fake_user.created_at = None
            fake_user.google_id = "goog_sub"

            mock_user_service_instance.create_or_get_user.return_value = fake_user

            # Mock DB logic for _find_or_create_google_user
            chain = mock_supabase.table.return_value.select.return_value.eq.return_value
            chain.execute.return_value = MagicMock(data=[])  # No existing user

            login_response = await auth_service.exchange_google_code("code", "ver", "redir")

            assert login_response.access_token is not None
            assert login_response.user.email == "t@gmail.com"

    @pytest.mark.asyncio
    async def test_exchange_google_code_http_error(self, auth_service):
        with patch(
            "services.google_auth_service.google_auth_service.exchange_google_code", new_callable=AsyncMock
        ) as mock_exchange:
            mock_exchange.side_effect = ValueError("Code exchange failed")

            with pytest.raises(ValueError, match="Code exchange failed"):
                await auth_service.exchange_google_code("code", "ver", "redir")
