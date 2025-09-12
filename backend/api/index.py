# Vercel serverless function handler
import os
import sys
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import the FastAPI app from main.py
try:
    from main import app
    print("✅ Successfully imported app from main.py")
except ImportError as e:
    print(f"❌ Failed to import from main.py: {e}")
    # Fallback: create a minimal app
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/health")
    async def health_check():
        return {"status": "error", "message": "Failed to import main app"}

# Export the app for Vercel
# Vercel will automatically detect the 'app' variable
