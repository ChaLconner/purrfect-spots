import sys
from pathlib import Path

# Add the backend directory to the Python path
# so that Vercel can find the 'main' module correctly.
backend_dir = Path(__file__).resolve().parent.parent.joinpath('backend')
sys.path.insert(0, str(backend_dir))

from main import app  # noqa: F401, E402

