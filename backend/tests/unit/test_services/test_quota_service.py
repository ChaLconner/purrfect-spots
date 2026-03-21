from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from services.quota_service import QuotaService


@pytest.fixture
def mock_supabase():
    mock = Mock()
    mock.table = Mock()
    mock.rpc = Mock()

    # Builder pattern mock for table queries
    builder = MagicMock()
    mock.table.return_value = builder
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.gt.return_value = builder
    builder.is_.return_value = builder
    builder.maybe_single.return_value = builder
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

    # Mock global system stats check
    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 100}

    # Mock user recent uploads check
    mock_cat_res = Mock()
    mock_cat_res.count = 2  # User has 2 uploads
    mock_cat_res.data = []

    # Apply side_effect to table queries (system stats -> cat photos)
    mock_supabase.table.return_value.execute.side_effect = [mock_sys_res, mock_cat_res]

    # Mock RPC increment
    mock_inc_res = Mock()
    mock_inc_res.data = None  # RPC usually returns void or data
    mock_supabase.rpc.return_value.execute.return_value = mock_inc_res

    allowed = await service.check_and_increment("user1", False)
    assert allowed

    # Verify RPC called (increment happens if allowed)
    mock_supabase.rpc.assert_called_once()
    assert mock_supabase.rpc.call_args[0][0] == "increment_usage"


@pytest.mark.asyncio
async def test_check_and_increment_over_limit_free(mock_supabase):
    service = QuotaService(mock_supabase)

    # Mock global check
    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 100}

    # Mock usage count > limit (Free limit 5)
    mock_cat_res = Mock()
    mock_cat_res.count = 6
    mock_cat_res.data = []

    mock_supabase.table.return_value.execute.side_effect = [mock_sys_res, mock_cat_res]

    # Patch FREE_LIMIT for test reliability
    with patch.object(QuotaService, "FREE_LIMIT", 5):
        allowed = await service.check_and_increment("user1", False)
        assert not allowed

    # RPC should NOT be called if over quota
    mock_supabase.rpc.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_increment_over_limit_pro(mock_supabase):
    service = QuotaService(mock_supabase)

    # Scenerios:
    # 1. Under limit (40)
    # 2. Over limit (51)

    # We need to setup side_effect for multiple check_and_increment calls
    # Call 1: sys_stats, cat_photos(40) -> Allowed -> RPC called
    # Call 2: sys_stats, cat_photos(51) -> Not Allowed -> RPC not called

    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 100}

    mock_cat_res_1 = Mock()
    mock_cat_res_1.count = 40

    mock_cat_res_2 = Mock()
    mock_cat_res_2.count = 51

    mock_supabase.table.return_value.execute.side_effect = [
        mock_sys_res,
        mock_cat_res_1,  # Call 1
        mock_sys_res,
        mock_cat_res_2,  # Call 2
    ]

    mock_inc_res = Mock()
    mock_supabase.rpc.return_value.execute.return_value = mock_inc_res

    # Patch PRO_LIMIT for test
    with patch.object(QuotaService, "PRO_LIMIT", 50):
        # First call: Under limit
        allowed = await service.check_and_increment("user1", True)
        assert allowed

        # Second call: Over limit
        allowed = await service.check_and_increment("user1", True)
        assert not allowed

    # Verify RPC called EXACTLY ONCE (for the successful call)
    mock_supabase.rpc.assert_called_once()


@pytest.mark.asyncio
async def test_check_and_increment_system_limit(mock_supabase):
    service = QuotaService(mock_supabase)

    # Mock global check > limit
    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 2001}

    # System limit checked before user quota, so execute called once
    mock_supabase.table.return_value.execute.side_effect = [mock_sys_res]

    allowed = await service.check_and_increment("user1", True)
    assert not allowed

    # Verify increment NOT called
    mock_supabase.rpc.assert_not_called()
