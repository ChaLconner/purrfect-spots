# Vercel serverless function handler
import os
import sys

# Add the current directory and parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Import the FastAPI app
from main import app

# For Vercel Python runtime, just export the app
# Vercel handles ASGI automatically for FastAPI apps
