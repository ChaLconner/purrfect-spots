import sys
from pathlib import Path

# Add the parent directory (backend) to the Python path
# so that Vercel can find the 'main' module correctly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: F401, E402

__all__ = ["app"]
