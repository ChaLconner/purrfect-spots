"""
Vercel serverless function entry point for FastAPI application.
This module imports and exposes the FastAPI app for Vercel's Python runtime.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import the FastAPI application
from main import app

# Additional CORS handling for Vercel
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Add CORS headers to all responses for Vercel deployment"""
    response = await call_next(request)
    
    origin = request.headers.get("origin")
    allowed_origins = [
        "https://purrfect-spots.vercel.app",
        "https://purrfect-spots-frontend.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        # Fallback for development
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response

# Vercel expects the ASGI application to be called 'app'
# But we'll also export it as 'handler' for compatibility
handler = app