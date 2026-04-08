from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.quota_service import QuotaService


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    mock.table = MagicMock()
    mock.rpc = MagicMock()

    # Builder pattern mock for table queries
    builder = MagicMock()
    mock.table.return_value = builder
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.gt.return_value = builder
    builder.gte.return_value = builder
    builder.lt.return_value = builder
    builder.lte.return_value = builder
    builder.is_.return_value = builder
    builder.order.return_value = builder
    builder.maybe_single.return_value = builder
    builder.single.return_value = builder
    # Execute is the final call - MUST be async
    builder.execute = AsyncMock()

    # Builder for RPC
    rpc_builder = MagicMock()
    mock.rpc.return_value = rpc_builder
    rpc_builder.execute = AsyncMock()

    return mock


@pytest.mark.asyncio
async def test_check_and_increment_under_limit(mock_supabase):
    service = QuotaService(mock_supabase)

    # 1. System stats check (system_daily_stats)
    mock_sys_res = MagicMock()
    mock_sys_res.data = {"total_uploads": 100}

    # 2. User usage check (cat_photos)
    mock_cat_res = MagicMock()
    # Usage check now returns timestamps
    now = datetime.now(UTC)
    mock_cat_res.data = [{"uploaded_at": (now - timedelta(hours=1)).isoformat()}]

    # Apply side_effect for sequential table()....execute() calls
    mock_supabase.table.return_value.execute.side_effect = [mock_sys_res, mock_cat_res]

    # Mock RPC increment
    mock_inc_res = MagicMock()
    mock_inc_res.data = None
    mock_supabase.rpc.return_value.execute.return_value = mock_inc_res

    allowed = await service.check_and_increment("user1", False)
    assert allowed is True

    # Verify RPC called (increment happens if allowed)
    mock_supabase.rpc.assert_called_once()
    assert mock_supabase.rpc.call_args[0][0] == "increment_usage"


@pytest.mark.asyncio
async def test_check_and_increment_over_limit_free(mock_supabase):
    service = QuotaService(mock_supabase)

    # 1. System stats (ok)
    mock_sys_res = MagicMock()
    mock_sys_res.data = {"total_uploads": 100}

    # 2. User usage (over limit, Free limit is 5)
    mock_cat_res = MagicMock()
    now = datetime.now(UTC)
    # 6 uploads within last hour
    mock_cat_res.data = [{"uploaded_at": (now - timedelta(minutes=i)).isoformat()} for i in range(6)]

    mock_supabase.table.return_value.execute.side_effect = [mock_sys_res, mock_cat_res]

    # Patch FREE_LIMIT for test reliability
    with patch.object(service, "FREE_LIMIT", 5):
        allowed = await service.check_and_increment("user1", False)
        assert allowed is False

    # RPC should NOT be called if over quota
    mock_supabase.rpc.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_increment_over_limit_pro(mock_supabase):
    service = QuotaService(mock_supabase)
    service.PRO_LIMIT = 50

    # Test Pro user over limit (51)
    mock_sys_res = MagicMock()
    mock_sys_res.data = {"total_uploads": 100}

    mock_cat_res = MagicMock()
    now = datetime.now(UTC)
    mock_cat_res.data = [{"uploaded_at": (now - timedelta(minutes=i)).isoformat()} for i in range(51)]

    mock_supabase.table.return_value.execute.side_effect = [mock_sys_res, mock_cat_res]

    allowed = await service.check_and_increment("user1", True)
    assert allowed is False
    mock_supabase.rpc.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_increment_system_limit(mock_supabase):
    service = QuotaService(mock_supabase)
    service.GLOBAL_SYSTEM_LIMIT = 2000

    # Mock system stats over limit
    mock_sys_res = MagicMock()
    mock_sys_res.data = {"total_uploads": 2001}

    mock_supabase.table.return_value.execute.side_effect = [mock_sys_res]

    allowed = await service.check_and_increment("user1", True)
    assert allowed is False
    mock_supabase.rpc.assert_not_called()
