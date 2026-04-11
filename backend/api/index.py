import sys
from pathlib import Path

# Add the parent directory (backend) to the Python path
# so that Vercel can find the 'main' module correctly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mock structlog if it's missing to prevent startup crashes
try:
    import structlog  # type: ignore[import-untyped, unused-ignore] # noqa: F401
except ImportError:
    import logging
    from typing import Any, cast

    class DummyStructlog:
        def get_logger(self, *args: Any, **kwargs: Any) -> Any:
            return logging.getLogger("purrfect_spots.fallback")

    sys.modules["structlog"] = cast(Any, DummyStructlog())

from main import app  # noqa: F401, E402

__all__ = ["app"]
