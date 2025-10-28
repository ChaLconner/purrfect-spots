import os
from typing import List
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

# Import authentication modules
from routes import auth_manual, auth_google, profile, upload, cat_detection
from dependencies import get_supabase_client

# Load .env from backend directory
from pathlib import Path
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

app = FastAPI(
    title="PurrFect Spots API",
    description="API for sharing cat photos with locations and OAuth authentication",
    version="2.0.0"
)

# Exception handlers (add before middleware and routers)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled Exception: {exc}")
    print(f"Exception type: {type(exc)}")
    print(f"Exception traceback: {exc.__traceback__}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"}  # CORS fallback (dev only!)
    )

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    print(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"}  # CORS fallback
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "errors": exc.errors()},
        headers={"Access-Control-Allow-Origin": "*"}  # CORS fallback
    )

# CORS middleware must be added BEFORE including routers
# List of allowed origins - include your frontend domain
allowed_origins = [
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Vite default port
    "https://purrfect-spots.vercel.app",  # Custom domain if applicable
    "https://purrfect-spots-backend.vercel.app"  # Backend URL for direct API access
]

# Add any additional origins from environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    env_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    allowed_origins.extend(env_origins)

# In Vercel environment, automatically add the deployment URL
if os.getenv("VERCEL_URL"):
    vercel_url = f"https://{os.getenv('VERCEL_URL')}"
    if vercel_url not in allowed_origins:
        allowed_origins.append(vercel_url)

print(f"CORS allowed origins: {allowed_origins}")

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "healthy", "message": "PurrFect Spots API is running"}

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "PurrFect Spots API is running"}

# CORS preflight handler for all routes
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle CORS preflight requests"""
    origin = request.headers.get("origin")
    
    # Check if origin is allowed
    if origin in allowed_origins:
        return JSONResponse(
            content={"message": "OK"},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",
            }
        )
    else:
        # For development, allow all origins (remove in production)
        return JSONResponse(
            content={"message": "OK"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
                "Access-Control-Max-Age": "86400",
            }
        )

# Include routers AFTER middleware
app.include_router(auth_manual.router)
app.include_router(auth_google.router)
app.include_router(profile.router)
app.include_router(upload.router)
app.include_router(cat_detection.router)

# Pydantic models
class CatLocation(BaseModel):
    id: str
    image_url: str
    latitude: float
    longitude: float
    description: str | None = None
    location_name: str | None = None
    uploaded_at: str | None = None

@app.get("/api/gallery")
async def get_gallery(supabase = Depends(get_supabase_client)):
    """Get all cat images from Supabase for gallery display."""
    try:
        resp = (
            supabase.table("cat_photos")
            .select("*")
            .order("uploaded_at", desc=True)
            .execute()
        )
        if not resp.data:
            return {"images": []}
        
        images = []
        for photo in resp.data:
            images.append({
                "id": photo.get("id"),
                "image_url": photo.get("image_url"),
                "description": photo.get("description"),
                "latitude": photo.get("latitude"),
                "longitude": photo.get("longitude"),
                "uploaded_at": photo.get("uploaded_at"),
            })
        
        return {"images": images}
        
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch gallery images: {str(e)}"
        )


@app.get("/locations", response_model=List[CatLocation])
async def get_locations(request: Request, supabase = Depends(get_supabase_client)):
    """Get all cat locations from Supabase."""
    try:
        resp = (
            supabase.table("cat_photos")
            .select("*")
            .order("uploaded_at", desc=True)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="No data returned from Supabase")
        return resp.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.options("/locations")
async def locations_options(request: Request):
    """Handle CORS preflight for locations endpoint"""
    origin = request.headers.get("origin")
    
    if origin in allowed_origins:
        return JSONResponse(
            content={"message": "OK"},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",
            }
        )
    else:
        return JSONResponse(
            content={"message": "OK"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin",
                "Access-Control-Max-Age": "86400",
            }
        )

# Vercel expects this to be available
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)