import sys
import os

# Add the parent directory (backend) to the Python path
# so that Vercel can find the 'main' module correctly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: F401
