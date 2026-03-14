from unittest.mock import AsyncMock, MagicMock

import pytest

from services.report_service import ReportService


class TestReportService:
    @pytest.mark.asyncio
    async def test_create_report_success(self):
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute = AsyncMock(return_value=MagicMock(data=[{"id": "report-123"}]))

        service = ReportService(mock_supabase)
        result = await service.create_report("photo-123", "user-123", "spam", "detail")

        assert result["id"] == "report-123"
        mock_table.insert.assert_called_once_with(
            {
                "photo_id": "photo-123",
                "reporter_id": "user-123",
                "reason": "spam",
                "details": "detail",
                "status": "pending",
            }
        )

    @pytest.mark.asyncio
    async def test_create_report_failure(self):
        mock_supabase = MagicMock()
        mock_execute = AsyncMock(return_value=MagicMock(data=[]))
        mock_supabase.table.return_value.insert.return_value.execute = mock_execute

        service = ReportService(mock_supabase)
        with pytest.raises(ValueError, match="Failed to create report"):
            await service.create_report("photo-123", "user-123", "spam")

    @pytest.mark.asyncio
    async def test_get_user_reports_success(self):
        mock_supabase = MagicMock()
        mock_execute = AsyncMock(return_value=MagicMock(data=[{"id": "r1"}]))
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute = mock_execute

        service = ReportService(mock_supabase)
        reports = await service.get_user_reports("user-123")
        assert len(reports) == 1
        assert reports[0]["id"] == "r1"

    @pytest.mark.asyncio
    async def test_get_user_reports_error(self):
        mock_supabase = MagicMock()
        mock_supabase.table.side_effect = Exception("DB Error")

        service = ReportService(mock_supabase)
        reports = await service.get_user_reports("user-123")
        assert reports == []
