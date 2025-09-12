"""
Vercel entry point for the FastAPI application.
This file serves as the serverless function handler for Vercel deployment.
"""

import sys
import os

# Add the backend directory to the Python path so we can import from main.py
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Import the FastAPI app from main.py
from main import app

# Export the app for Vercel
handler = app