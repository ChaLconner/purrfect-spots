import sys
from pathlib import Path

# Add the backend directory to the Python path
# so that Vercel can find the 'main' module correctly.
backend_dir = Path(__file__).resolve().parent.parent.joinpath("backend")
sys.path.insert(0, str(backend_dir))

# Mock structlog if it's missing to prevent startup crashes
try:
    import structlog  # noqa: F401
except ImportError:
    import logging
    class DummyStructlog:
        def get_logger(self, *args, **kwargs):
            return logging.getLogger("purrfect_spots.fallback")
    sys.modules["structlog"] = DummyStructlog()

from main import app  # noqa: F401, E402

__all__ = ["app"]
