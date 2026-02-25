# Vercel FastAPI entrypoint
# Vercel's Python runtime looks for an 'app' object in this file.
# Re-export the FastAPI app from main.py so Vercel can find it.
from main import app  # noqa: F401
