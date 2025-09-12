"""
Vercel serverless function entry point for FastAPI application.
This module imports and exposes the FastAPI app for Vercel's Python runtime.
"""

# Import the FastAPI application
from main import app

# Vercel expects the ASGI application to be called 'app'
# But we'll also export it as 'handler' for compatibility
handler = app