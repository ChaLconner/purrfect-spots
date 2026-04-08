import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ========== Environment Setup ==========
# These must be set BEFORE importing anything that uses them
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters-long!!"
os.environ["JWT_REFRESH_SECRET"] = "test-refresh-secret-at-least-32-characters!!"
os.environ["STRIPE_PRO_PRICE_ID"] = "price_pro_test"

# Disable Redis via env var (fallback if mock fails)
os.environ["REDIS_URL"] = ""

# Mock mcp module to prevent import hangs during tests
mock_mcp = MagicMock()
sys.modules["mcp"] = mock_mcp
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.lowlevel"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = MagicMock()

# Mock structlog if it is not installed in the local test environment
try:
    import structlog  # noqa: F401
except ImportError:
    mock_structlog = MagicMock()
    mock_structlog.get_logger.return_value = MagicMock()
    sys.modules["structlog"] = mock_structlog

# Mock sentry_sdk.integrations.mcp to prevent "MCP SDK not installed" error in main.py
mock_sentry_mcp = MagicMock()

try:
    from sentry_sdk.integrations import Integration

    class MockMCPIntegration(Integration):
        identifier = "mcp"

        @staticmethod
        def setup_once(*args, **kwargs):
            pass

        def setup_once_with_options(self, *args, **kwargs):
            pass

        def __init__(self, *args, **kwargs):
            pass

    mock_sentry_mcp.MCPIntegration = MockMCPIntegration
    sys.modules["sentry_sdk.integrations.mcp"] = mock_sentry_mcp
except ImportError:
    pass

# Now we can import the app
from main import app


@pytest.fixture(autouse=True)
def disable_rate_limit():
    \"\"\"Disable rate limiting for all tests\"\"\"
    from limiter import auth_limiter, limiter, strict_limiter, upload_limiter

    limiters = [limiter, auth_limiter, strict_limiter, upload_limiter]

    # Store initial states
    initial_states = [limiter_instance.enabled for limiter_instance in limiters]

    # Disable all
    for limiter_instance in limiters:
        limiter_instance.enabled = False

    yield

    # Restore initial states
    for i, limiter_instance in enumerate(limiters):
        limiter_instance.enabled = initial_states[i]


@pytest.fixture(autouse=True)
def mock_redis_service():
    \"\"\"Globally mock redis_service to prevent external connections and hangs during tests\"\"\"
    from unittest.mock import AsyncMock, patch

    from services.redis_service import redis_service

    # Methods to mock based on RedisService implementation
    mocks = {
        "get": AsyncMock(return_value=None),
        "set": AsyncMock(return_value=True),
        "delete": AsyncMock(return_value=True),
        "delete_pattern": AsyncMock(return_value=0),
        "ping": AsyncMock(return_value=True),
    }

    with patch.multiple(redis_service, **mocks):
        yield


@pytest.fixture
def client():
    \"\"\"Create a test client for the FastAPI app\"\"\"
    return TestClient(app)


@pytest.fixture
def mock_supabase_admin():
    \"\"\"Mock the Supabase admin client\"\"\"
    with patch(\"dependencies.get_async_supabase_admin_client\") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_supabase_auth():
    \"\"\"Mock the Supabase auth client\"\"\"
    with patch(\"dependencies.get_supabase_auth\") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def auth_headers():
    \"\"\"Standard authorization headers for tests\"\"\"
    return {\"Authorization\": \"Bearer test-token\"}


@pytest.fixture
def admin_auth_headers():
    \"\"\"Admin authorization headers for tests\"\"\"
    return {\"Authorization\": \"Bearer admin-test-token\"}
