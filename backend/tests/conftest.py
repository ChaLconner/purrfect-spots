"""
Pytest configuration and fixtures for backend tests

# nosec python:S2068 - Hardcoded tokens and credentials in this file are intentional test fixtures
# These are not real credentials; they are used only for unit testing
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Disable Sentry during tests to prevent exit issues
os.environ["SENTRY_DSN"] = ""
# Disable Redis to prevent connection hangs
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
    sys.modules["limiter"].limiter = MagicMock()
    sys.modules["limiter"].limiter.limit = lambda x: lambda f: f  # Mock decorator


# Mock mcp module if it causes issues (e.g. issues with anyio on windows)
# Force mock mcp module to prevent import hangs during tests
mock_mcp = MagicMock()
sys.modules["mcp"] = mock_mcp
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.lowlevel"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = MagicMock()

# Mock sentry_sdk.integrations.mcp to prevent "MCP SDK not installed" error in main.py
mock_sentry_mcp = MagicMock()

try:
    from sentry_sdk.integrations import Integration

    class MockMCPIntegration(Integration):
        identifier = "mcp"

        @staticmethod
        def setup_once(*args, **kwargs):
            pass

        def __init__(self, *args, **kwargs):
            pass
except ImportError:

    class MockMCPIntegration:
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


# Disable rate limiting for all tests
@pytest.fixture(autouse=True)
def disable_rate_limit():
    """Disable rate limiting for all tests"""
    from limiter import auth_limiter, limiter, strict_limiter, upload_limiter

    limiters = [limiter, auth_limiter, strict_limiter, upload_limiter]

    # Store initial states
    initial_states = [limiter_instance.enabled for limiter_instance in limiters]

    # Disable all
    for limiter_instance in limiters:
        limiter_instance.enabled = False

    yield

    # Restore states
    for i, limiter_instance in enumerate(limiters):
        limiter_instance.enabled = initial_states[i]


from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


def _create_mock_supabase_client():
    """Helper to create a standard mock Supabase client"""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.neq.return_value = mock
    mock.single.return_value = mock
    mock.maybe_single.return_value = mock
    mock.order.return_value = mock
    mock.range.return_value = mock
    mock.limit.return_value = mock
    mock.offset.return_value = mock
    mock.or_.return_value = mock
    mock.contains.return_value = mock
    mock.is_.return_value = mock
    mock.gte.return_value = mock
    mock.lte.return_value = mock
    mock.text_search.return_value = mock
    mock.rpc.return_value = mock
    mock.not_.is_.return_value = mock  # Handling .not_.is_ chain
    from unittest.mock import AsyncMock

    mock.execute = AsyncMock(return_value=MagicMock(data=[], count=0))
    return mock


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client"""
    return _create_mock_supabase_client()


@pytest.fixture
def mock_supabase_admin():
    """Create a mock Supabase admin client"""
    return _create_mock_supabase_client()


@pytest.fixture(autouse=True)
def mock_async_supabase():
    """
    Mock the async_supabase client with proper async behavior.
    """
    from unittest.mock import AsyncMock, patch

    with patch("utils.async_client.async_supabase") as mock:
        # Use AsyncMock for methods that are awaited
        # Default successful but empty returns
        mock.rpc = AsyncMock(return_value=[])
        mock.select = AsyncMock(return_value=[])
        mock.count = AsyncMock(return_value=0)
        yield mock


class MockUser:
    """Mock user class for testing"""

    def __init__(self):
        self.id = "00000000-0000-4000-a000-000000000123"
        self.email = "test@example.com"
        self.name = "Test User"
        self.picture = "https://example.com/avatar.jpg"
        self.bio = "Test bio"
        self.is_pro = False
        self.created_at = "2024-01-01T00:00:00Z"


@pytest.fixture
def mock_user():
    """Create a mock authenticated user"""
    return MockUser()


@pytest.fixture
def mock_cat_photo():
    """Create a mock cat photo record"""
    return {
        "id": "test-photo-123",
        "user_id": "00000000-0000-4000-a000-000000000123",
        "location_name": "Test Cat Spot",
        "description": "A cute cat #orange #friendly",
        "tags": ["orange", "friendly"],
        "latitude": 13.7563,
        "longitude": 100.5018,
        "image_url": "https://example.com/cat.jpg",
        "uploaded_at": "2024-01-01T12:00:00Z",
    }


@pytest.fixture
def auth_headers():
    """Create mock authentication headers"""
    return {"Authorization": "Bearer test-token-123"}


@pytest.fixture
def sample_image_bytes():
    """Create sample JPEG image bytes for testing"""
    import io

    from PIL import Image

    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_large_image_bytes():
    """Create a large image for resize testing"""
    import io

    from PIL import Image

    # Create a large test image
    img = Image.new("RGB", (3000, 2000), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=100)
    return buffer.getvalue()
