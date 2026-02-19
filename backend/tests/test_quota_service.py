from unittest.mock import Mock, patch

import pytest

from services.quota_service import QuotaService


@pytest.fixture
def mock_supabase():
    mock = Mock()
    mock.table = Mock()
    mock.rpc = Mock()

    # Builder pattern mock for table queries
    builder = Mock()
    mock.table.return_value = builder
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.maybe_single.return_value = builder
    # Execute is the final call
    builder.execute = Mock()

    # Builder for RPC
    rpc_builder = Mock()
    mock.rpc.return_value = rpc_builder
    rpc_builder.execute = Mock()

    return mock


@pytest.mark.asyncio
async def test_check_and_increment_under_limit(mock_supabase):
    service = QuotaService(mock_supabase)

    # Mock global check
    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 100}
    mock_supabase.table.return_value.execute.return_value = mock_sys_res

    # Mock increment
    mock_inc_res = Mock()
    mock_inc_res.data = 3  # New count is 3
    mock_supabase.rpc.return_value.execute.return_value = mock_inc_res

    allowed = await service.check_and_increment("user1", False)
    assert allowed

    # Verify RPC called
    mock_supabase.rpc.assert_called_once()
    assert mock_supabase.rpc.call_args[0][0] == "increment_usage"


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_check_and_increment_over_limit_free(mock_supabase):
    service = QuotaService(mock_supabase)

    # Mock global check
    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 100}
    mock_supabase.table.return_value.execute.return_value = mock_sys_res

    # Mock increment to return value > limit (5 for free)
    mock_inc_res = Mock()
    mock_inc_res.data = 6
    mock_supabase.rpc.return_value.execute.return_value = mock_inc_res

    # Patch FREE_LIMIT for test
    with patch.object(QuotaService, "FREE_LIMIT", 5):
        allowed = await service.check_and_increment("user1", False)
        assert not allowed


@pytest.mark.asyncio
async def test_check_and_increment_over_limit_pro(mock_supabase):
    service = QuotaService(mock_supabase)

    # Mock global check
    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 100}
    mock_supabase.table.return_value.execute.return_value = mock_sys_res

    # Mock increment to return value <= pro limit (50)
    mock_inc_res = Mock()
    mock_inc_res.data = 40
    mock_supabase.rpc.return_value.execute.return_value = mock_inc_res

    # Patch PRO_LIMIT for test
    with patch.object(QuotaService, "PRO_LIMIT", 50):
        allowed = await service.check_and_increment("user1", True)
        assert allowed

        # Over limit
        mock_inc_res.data = 51
        # Check again
        allowed = await service.check_and_increment("user1", True)
        assert not allowed


@pytest.mark.asyncio
async def test_check_and_increment_system_limit(mock_supabase):
    service = QuotaService(mock_supabase)

    # Mock global check > limit
    mock_sys_res = Mock()
    mock_sys_res.data = {"total_uploads": 2001}
    mock_supabase.table.return_value.execute.return_value = mock_sys_res

    allowed = await service.check_and_increment("user1", True)
    assert not allowed

    # Verify increment NOT called
    mock_supabase.rpc.assert_not_called()
