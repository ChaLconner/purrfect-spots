from unittest.mock import AsyncMock, MagicMock, patch

from postgrest.types import CountMethod

from main import app
from middleware.auth_middleware import get_current_user
from schemas.user import User


class TestAdminStatsSummary:
    def test_summary_uses_exact_counts_for_dashboard_totals(self, client, mock_supabase_admin) -> None:
        admin_user = User(
            id="admin-123",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["system:stats"],
        )
        app.dependency_overrides[get_current_user] = lambda: admin_user

        mock_supabase_admin.execute = AsyncMock(
            side_effect=[
                MagicMock(count=101),  # users
                MagicMock(count=202),  # photos
                MagicMock(count=3),  # pending reports
                MagicMock(count=33),  # total reports
                MagicMock(data={"users": [], "photos": [], "reports": []}),  # trends rpc
                MagicMock(data=[{"month_timestamp": "2026-01-01T00:00:00", "new_users": 1}]),  # monthly rpc
            ]
        )

        try:
            with patch(
                "routes.admin.stats.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ):
                response = client.get("/api/v1/admin/summary")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["stats"] == {
            "total_users": 101,
            "total_photos": 202,
            "pending_reports": 3,
            "total_reports": 33,
        }

        mock_supabase_admin.select.assert_any_call("id", count=CountMethod.exact)

    def test_monthly_fallback_returns_bounded_degraded_points_metric(self, client, mock_supabase_admin) -> None:
        admin_user = User(
            id="admin-123",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["system:stats"],
        )
        app.dependency_overrides[get_current_user] = lambda: admin_user

        monthly_count_response = MagicMock(count=2)
        mock_supabase_admin.execute = AsyncMock(
            side_effect=[
                MagicMock(data=[]),
                *([monthly_count_response] * 36),
            ]
        )

        try:
            with patch(
                "routes.admin.stats.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ):
                response = client.get("/api/v1/admin/monthly?year=2026")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["year"] == 2026
        assert len(payload["data"]) == 12
        assert payload["data"][0]["new_users"] == 2
        assert payload["data"][0]["new_photos"] == 2
        assert payload["data"][0]["resolved_reports"] == 2
        assert payload["data"][0]["points_earned"] == 0
        assert payload["data"][0]["points_earned_degraded"] is True
