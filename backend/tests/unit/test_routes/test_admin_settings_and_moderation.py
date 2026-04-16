from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dependencies import get_notification_service
from main import app
from middleware.auth_middleware import get_current_user
from routes.admin.settings import email_service
from schemas.user import User


class TestAdminSettingsRoutes:
    @pytest.fixture(autouse=True)
    def make_supabase_chainable(self, mock_supabase_admin):
        mock_supabase_admin.in_.return_value = mock_supabase_admin
        return mock_supabase_admin

    @pytest.fixture
    def admin_user(self):
        return User(
            id="00000000-0000-4000-a000-000000000111",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["system:settings"],
        )

    @pytest.fixture
    def override_admin(self, admin_user):
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_get_all_settings_success(self, client, override_admin, mock_supabase_admin) -> None:
        mock_supabase_admin.execute.return_value = MagicMock(
            data=[
                {
                    "key": "feature_flag",
                    "value": True,
                    "type": "boolean",
                    "description": "Toggle feature",
                    "category": "general",
                    "is_public": False,
                    "is_encrypted": False,
                    "requires_approval": False,
                    "updated_at": "2026-03-28T00:00:00Z",
                    "updated_by": None,
                }
            ]
        )

        with patch(
            "routes.admin.settings.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/settings")

        assert response.status_code == 200
        assert response.json()[0]["is_encrypted"] is False

    def test_update_setting_without_approval_returns_updated_config(
        self, client, override_admin, admin_user, mock_supabase_admin
    ) -> None:
        mock_supabase_admin.execute.side_effect = [
            MagicMock(data={"value": False, "requires_approval": False}),
            MagicMock(
                data={
                    "key": "feature_flag",
                    "value": True,
                    "type": "boolean",
                    "description": "Toggle feature",
                    "category": "general",
                    "is_public": False,
                    "is_encrypted": False,
                    "requires_approval": False,
                    "updated_at": "2026-03-28T00:00:00Z",
                    "updated_by": admin_user.id,
                }
            ),
            MagicMock(),
        ]

        with patch(
            "routes.admin.settings.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.put("/api/v1/admin/settings/feature_flag", json={"value": True})

        assert response.status_code == 200
        assert response.json()["value"] is True

    def test_get_pending_changes_enriches_current_value_and_requester_email(
        self, client, override_admin, mock_supabase_admin
    ) -> None:
        mock_supabase_admin.execute.side_effect = [
            MagicMock(
                data=[
                    {
                        "id": "00000000-0000-4000-a000-000000000222",
                        "config_key": "feature_flag",
                        "proposed_value": True,
                        "requester_id": "00000000-0000-4000-a000-000000000333",
                        "approver_id": None,
                        "status": "pending",
                        "rejection_reason": None,
                        "created_at": "2026-03-28T00:00:00Z",
                        "updated_at": "2026-03-28T00:00:00Z",
                        "requester": {"email": "maker@example.com"},
                    }
                ]
            ),
            MagicMock(data=[{"key": "feature_flag", "value": False}]),
        ]

        with patch(
            "routes.admin.settings.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/settings/pending")

        assert response.status_code == 200
        payload = response.json()[0]
        assert payload["requester_email"] == "maker@example.com"
        assert payload["current_value"] is False

    def test_approve_change_uses_admin_name(self, client, override_admin, admin_user, mock_supabase_admin) -> None:
        mock_supabase_admin.execute.side_effect = [
            MagicMock(
                data={
                    "id": "00000000-0000-4000-a000-000000000222",
                    "config_key": "feature_flag",
                    "proposed_value": True,
                    "requester_id": "00000000-0000-4000-a000-000000000333",
                    "status": "pending",
                }
            ),
            MagicMock(data={"key": "feature_flag", "value": False}),
            MagicMock(
                data={
                    "key": "feature_flag",
                    "value": True,
                    "type": "boolean",
                    "description": "Toggle feature",
                    "category": "general",
                    "is_public": False,
                    "is_encrypted": False,
                    "requires_approval": True,
                    "updated_at": "2026-03-28T00:00:00Z",
                    "updated_by": admin_user.id,
                }
            ),
            MagicMock(),
            MagicMock(),
            MagicMock(data={"email": "maker@example.com"}),
        ]

        with (
            patch(
                "routes.admin.settings.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ),
            patch.object(
                email_service,
                "send_admin_config_result",
            ) as mock_send_result,
        ):
            response = client.post("/api/v1/admin/settings/approve/00000000-0000-4000-a000-000000000222", json={})

        assert response.status_code == 200
        mock_send_result.assert_called_once_with(
            "maker@example.com",
            "feature_flag",
            "approved",
            "Admin User",
        )

    def test_reject_change_uses_rejection_reason_payload(
        self, client, override_admin, admin_user, mock_supabase_admin
    ) -> None:
        mock_supabase_admin.execute.side_effect = [
            MagicMock(
                data={
                    "id": "00000000-0000-4000-a000-000000000222",
                    "config_key": "feature_flag",
                    "requester_id": "00000000-0000-4000-a000-000000000333",
                    "status": "pending",
                }
            ),
            MagicMock(),
            MagicMock(data={"email": "maker@example.com"}),
        ]

        with (
            patch(
                "routes.admin.settings.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ),
            patch.object(
                email_service,
                "send_admin_config_result",
            ) as mock_send_result,
        ):
            response = client.post(
                "/api/v1/admin/settings/reject/00000000-0000-4000-a000-000000000222",
                json={"rejection_reason": "Needs review"},
            )

        assert response.status_code == 200
        mock_send_result.assert_called_once_with(
            "maker@example.com",
            "feature_flag",
            "rejected",
            "Admin User",
            "Needs review",
        )

    def test_reject_change_rejects_already_processed_request(self, client, override_admin, mock_supabase_admin) -> None:
        mock_supabase_admin.execute.return_value = MagicMock(
            data={
                "id": "00000000-0000-4000-a000-000000000222",
                "config_key": "feature_flag",
                "requester_id": "00000000-0000-4000-a000-000000000333",
                "status": "approved",
            }
        )

        with patch(
            "routes.admin.settings.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.post(
                "/api/v1/admin/settings/reject/00000000-0000-4000-a000-000000000222",
                json={"rejection_reason": "Needs review"},
            )

        assert response.status_code == 404
        assert "already processed" in response.json()["detail"]


class TestAdminUserCacheInvalidation:
    @pytest.fixture(autouse=True)
    def make_supabase_chainable(self, mock_supabase_admin):
        mock_supabase_admin.in_.return_value = mock_supabase_admin
        return mock_supabase_admin

    @pytest.fixture
    def admin_user(self):
        return User(
            id="00000000-0000-4000-a000-000000000111",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["users:update"],
        )

    @pytest.fixture
    def override_admin(self, admin_user):
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_update_user_role_invalidates_auth_cache(self, client, override_admin, mock_supabase_admin) -> None:
        user_id = "00000000-0000-4000-a000-000000000999"
        role_id = "00000000-0000-4000-a000-000000000888"
        mock_supabase_admin.execute.side_effect = [
            MagicMock(data={"name": "Moderator"}),
            MagicMock(data=[{"id": user_id, "role_id": role_id}]),
            MagicMock(),
        ]

        with (
            patch(
                "routes.admin.users.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ),
            patch("routes.admin.users.invalidate_user_auth_cache") as mock_invalidate,
        ):
            response = client.put(f"/api/v1/admin/users/{user_id}/role", json={"role_id": role_id})

        assert response.status_code == 200
        mock_invalidate.assert_called_once_with(user_id)

    def test_ban_user_invalidates_auth_cache(self, client, override_admin, mock_supabase_admin) -> None:
        user_id = "00000000-0000-4000-a000-000000000999"
        mock_token_service = MagicMock()
        mock_token_service.blacklist_all_user_tokens = AsyncMock(return_value=1)
        mock_supabase_admin.execute.side_effect = [
            MagicMock(data={"email": "user@example.com", "roles": {"name": "user"}}),
            MagicMock(),
            MagicMock(),
        ]

        with (
            patch(
                "routes.admin.users.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ),
            patch("routes.admin.users.invalidate_user_auth_cache") as mock_invalidate,
            patch(
                "routes.admin.users.get_token_service",
                new_callable=AsyncMock,
                return_value=mock_token_service,
            ),
        ):
            response = client.post(f"/api/v1/admin/users/{user_id}/ban", json={"reason": "Violation"})

        assert response.status_code == 200
        mock_invalidate.assert_called_once_with(user_id)
        mock_token_service.blacklist_all_user_tokens.assert_awaited_once_with(user_id, reason="admin_ban")


class TestAdminCommentBulkDelete:
    @pytest.fixture(autouse=True)
    def make_supabase_chainable(self, mock_supabase_admin):
        mock_supabase_admin.in_.return_value = mock_supabase_admin
        return mock_supabase_admin

    @pytest.fixture
    def admin_user(self):
        return User(
            id="00000000-0000-4000-a000-000000000111",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["comments:manage"],
        )

    @pytest.fixture
    def override_admin(self, admin_user):
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_bulk_delete_comments_notifies_comment_authors(self, client, override_admin, mock_supabase_admin) -> None:
        notification_service = MagicMock()

        mock_supabase_admin.execute.side_effect = [
            MagicMock(),
            MagicMock(data=[{"user_id": "user-1"}, {"user_id": "user-2"}, {"user_id": "user-1"}]),
            MagicMock(),
            MagicMock(),
        ]

        with patch(
            "routes.admin.comments.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            app.dependency_overrides[get_notification_service] = lambda: notification_service
            try:
                response = client.post(
                    "/api/v1/admin/comments/bulk-delete",
                    json={"comment_ids": ["comment-1", "comment-2"]},
                )
            finally:
                app.dependency_overrides.pop(get_notification_service, None)

        assert response.status_code == 200
        called_user_ids = {call.kwargs["user_id"] for call in notification_service.create_notification.call_args_list}
        assert called_user_ids == {"user-1", "user-2"}


class TestAdminCommentModerationBan:
    @pytest.fixture
    def admin_user(self):
        return User(
            id="00000000-0000-4000-a000-000000000111",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["comments:manage"],
        )

    @pytest.fixture
    def override_admin(self, admin_user):
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_ban_user_by_comment_rejects_admin_targets(self, client, override_admin, mock_supabase_admin) -> None:
        notification_service = MagicMock()
        mock_supabase_admin.execute.side_effect = [
            MagicMock(data={"user_id": "00000000-0000-4000-a000-000000000999"}),
            MagicMock(data={"email": "other-admin@example.com", "roles": {"name": "admin"}}),
        ]

        with patch(
            "routes.admin.comments.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            app.dependency_overrides[get_notification_service] = lambda: notification_service
            try:
                response = client.post("/api/v1/admin/comments/comment-1/ban-user")
            finally:
                app.dependency_overrides.pop(get_notification_service, None)

        assert response.status_code == 400
        assert "Cannot ban an admin user" in response.json()["detail"]

    def test_ban_user_by_comment_invalidates_auth_state(self, client, override_admin, mock_supabase_admin) -> None:
        notification_service = MagicMock()
        mock_token_service = MagicMock()
        mock_token_service.blacklist_all_user_tokens = AsyncMock(return_value=1)
        target_user_id = "00000000-0000-4000-a000-000000000999"

        mock_supabase_admin.execute.side_effect = [
            MagicMock(data={"user_id": target_user_id}),
            MagicMock(data={"email": "user@example.com", "roles": {"name": "user"}}),
            MagicMock(),
            MagicMock(),
        ]

        with (
            patch(
                "routes.admin.comments.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ),
            patch("routes.admin.comments.invalidate_user_auth_cache") as mock_invalidate,
            patch(
                "routes.admin.comments.get_token_service",
                new_callable=AsyncMock,
                return_value=mock_token_service,
            ),
        ):
            app.dependency_overrides[get_notification_service] = lambda: notification_service
            try:
                response = client.post("/api/v1/admin/comments/comment-1/ban-user")
            finally:
                app.dependency_overrides.pop(get_notification_service, None)

        assert response.status_code == 200
        mock_invalidate.assert_called_once_with(target_user_id)
        mock_token_service.blacklist_all_user_tokens.assert_awaited_once_with(
            target_user_id,
            reason="comment_moderation_ban",
        )


class TestAdminCommentsListing:
    @pytest.fixture
    def admin_user(self):
        return User(
            id="00000000-0000-4000-a000-000000000111",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["comments:manage"],
        )

    @pytest.fixture
    def override_admin(self, admin_user):
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_list_all_comments_accepts_limit_alias(self, client, override_admin, mock_supabase_admin) -> None:
        mock_supabase_admin.execute = AsyncMock(
            side_effect=[
                MagicMock(
                    data=[
                        {
                            "id": "comment-1",
                            "user_id": "user-1",
                            "content": "hello",
                            "created_at": "2026-03-28T00:00:00Z",
                            "report_count": 0,
                        }
                    ],
                    count=1,
                ),
                MagicMock(data=[{"id": "user-1", "banned_at": None}]),
                MagicMock(data=[]),
            ]
        )

        with patch(
            "routes.admin.comments.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/comments?page=1&limit=100")

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["items"][0]["is_user_banned"] is False
        assert payload["items"][0]["violation_count"] == 0


class TestAdminUserProfileUpdates:
    @pytest.fixture
    def admin_user(self):
        return User(
            id="00000000-0000-4000-a000-000000000111",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["users:write"],
        )

    @pytest.fixture
    def override_admin(self, admin_user):
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_update_user_profile_requires_payload_fields(self, client, override_admin, mock_supabase_admin) -> None:
        with patch(
            "routes.admin.users.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.patch(
                "/api/v1/admin/users/00000000-0000-4000-a000-000000000999/profile",
                json={},
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "No valid fields provided"

    def test_update_user_profile_returns_not_found(self, client, override_admin, mock_supabase_admin) -> None:
        mock_supabase_admin.execute.return_value = MagicMock(data=[])

        with patch(
            "routes.admin.users.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.patch(
                "/api/v1/admin/users/00000000-0000-4000-a000-000000000999/profile",
                json={"name": "Updated Name"},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
