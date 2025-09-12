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

# Export the app for Vercel
# Vercel looks for 'app' variable by default
# No need for explicit handler
