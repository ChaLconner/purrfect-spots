import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ========== Environment Setup ==========
# These must be set BEFORE importing anything that uses them
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters-long!!"
os.environ["JWT_REFRESH_SECRET"] = "test-refresh-secret-key-at-least-32-chars-long"

# Set Stripe mock keys to avoid config warnings
os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock_secret_key"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_mock_webhook_secret"
os.environ["STRIPE_PRO_PRICE_ID"] = "price_pro_test"
os.environ["STRIPE_PRO_ANNUAL_PRICE_ID"] = "price_pro_annual_test"
os.environ["ENCRYPTION_KEY"] = "Y2hhbmdlbWVjaGFuZ2VtZWNoYW5nZW1lY2hhbmdlbWU="

# Set trusted proxies explicitly to avoid wildcard trust warning
os.environ["TRUSTED_PROXY_HOSTS"] = "127.0.0.1,::1"

# Disable Redis via env var (fallback if mock fails)
os.environ["REDIS_URL"] = ""

# Add backend directory to path so imports work
sys.path.append(str(Path(__file__).parent.parent))

# Mock bcrypt before it's imported by services to avoid PyO3 initialization error
try:
    import bcrypt  # noqa: F401
except (ImportError, RuntimeError, Exception):
    mock_bcrypt = MagicMock()
    mock_bcrypt.gensalt.return_value = b"$2b$12$test"
    mock_bcrypt.hashpw.return_value = b"hashed"
    mock_bcrypt.checkpw.return_value = True
    sys.modules["bcrypt"] = mock_bcrypt

# Mock supabase module if it cannot be imported
try:
    import supabase  # noqa: F401
except ImportError:
    mock_supabase_module = MagicMock()
    sys.modules["supabase"] = mock_supabase_module
    sys.modules["supabase.client"] = MagicMock()

# Mock google cloud modules if they are missing
try:
    import google.cloud.vision  # noqa: F401
except ImportError:
    # Logic to mock only the missing parts
    # We assume google package itself might exist because of google-auth
    mock_vision = MagicMock()
    sys.modules["google.cloud.vision"] = mock_vision

    # Ensure google.cloud exists as a module/package if not already
    if "google.cloud" not in sys.modules:
        sys.modules["google.cloud"] = MagicMock()

# Mock slowapi if not present
try:
    import slowapi  # noqa: F401
except ImportError:
    mock_slowapi = MagicMock()
    sys.modules["slowapi"] = mock_slowapi
    sys.modules["slowapi.errors"] = MagicMock()
    sys.modules["slowapi.util"] = MagicMock()
    # Mock limiter instance since it's used in decorators
    sys.modules["limiter"] = MagicMock()
    sys.modules["limiter"].limiter = MagicMock()  # type: ignore[attr-defined]
    sys.modules["limiter"].limiter.limit = lambda x: lambda f: f  # type: ignore[attr-defined]


# Mock mcp module if it causes issues (e.g. issues with anyio on windows)
# Force mock mcp module to prevent import hangs during tests
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


@pytest.fixture(autouse=True)
def clear_all_caches():
    \"\"\"Clear all memory and redis caches before every test to ensure test isolation\"\"\"
    from utils.cache import memory_cache

    memory_cache.clear()
    yield


@pytest.fixture
def client():
    \"\"\"Create a test client for the FastAPI app\"\"\"
    return TestClient(app)


def _create_mock_supabase_client():
    \"\"\"Helper to create a mock Supabase client with standard chaining\"\"\"
    client = MagicMock()
    table = MagicMock()
    client.table.return_value = table

    # Setup chainable methods
    chainable = ["select", "insert", "update", "delete", "eq", "is_", "limit", "order", "single"]
    for method in chainable:
        getattr(table, method).return_value = table

    # Setup execution results
    res = MagicMock()
    res.data = []
    res.count = 0
    table.execute = MagicMock(return_value=res)

    return client


@pytest.fixture
def mock_supabase_admin():
    \"\"\"Create a mock Supabase admin client\"\"\"
    return _create_mock_supabase_client()


@pytest.fixture(autouse=True)
def mock_boto3_client():
    \"\"\"Mock boto3 client to prevent real AWS calls during tests\"\"\"
    with patch("boto3.client") as mock:
        mock_s3 = MagicMock()
        mock.return_value = mock_s3
        yield mock_s3


@pytest.fixture(autouse=True)
def mock_async_supabase():
    \"\"\"
    Mock the async_supabase client with proper async behavior.
    \"\"\"
    # Mock acreate_client in utils.supabase_client
    with patch("utils.supabase_client.acreate_client", new_callable=AsyncMock) as mock_ac:
        mock_client = MagicMock()
        mock_ac.return_value = mock_client

        # Setup standard mock table/select chain
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        # List of methods that typically return 'self' for chaining
        chainable_methods = ["select", "insert", "update", "delete", "eq", "is_", "limit", "order", "single"]
        for method in chainable_methods:
            getattr(mock_table, method).return_value = mock_table

        # execute() must be an AsyncMock because it's awaited
        mock_query_result = MagicMock()
        mock_query_result.data = [{"id": 1}]  # Non-empty list to simulate success
        mock_query_result.count = 1
        mock_table.execute = AsyncMock(return_value=mock_query_result)

        # Setup RPC
        mock_rpc = MagicMock()
        mock_rpc.execute = AsyncMock(return_value=MagicMock(data=[]))
        mock_client.rpc.return_value = mock_rpc

        yield mock_client


class MockUser:
    \"\"\"Mock user class for testing\"\"\"

    def __init__(self):
        self.id = "00000000-0000-4000-a000-000000000123"
        self.email = "test@example.com"
        self.username = "testuser"
        self.name = "Test User"
        self.picture = "https://example.com/avatar.jpg"
        self.bio = "Test bio"
        self.is_pro = False
        self.created_at = "2024-01-01T00:00:00Z"
        self.banned_at = None


@pytest.fixture
def mock_supabase_auth():
    \"\"\"Mock the Supabase auth client\"\"\"
    with patch("dependencies.get_supabase_auth") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def auth_headers():
    \"\"\"Standard authorization headers for tests\"\"\"
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def admin_auth_headers():
    \"\"\"Admin authorization headers for tests\"\"\"
    return {"Authorization": "Bearer admin-test-token"}
