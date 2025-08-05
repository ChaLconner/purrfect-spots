import os
from typing import List

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

load_dotenv()

app = FastAPI(
    title="PurrFect Spots API",
    description="API for sharing cat photos with locations and OAuth authentication",
    version="2.0.0"
)

# ✅ Exception handlers (add before middleware and routers)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"🔥 Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers={"Access-Control-Allow-Origin": "*"}  # CORS fallback (dev only!)
    )

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    print(f"🔥 HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"}  # CORS fallback
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"🔥 Validation Error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "errors": exc.errors()},
        headers={"Access-Control-Allow-Origin": "*"}  # CORS fallback
    )

# ✅ CORS middleware must be added BEFORE including routers
# Get allowed origins from environment variable or use defaults
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    # Default origins for development and production
    allowed_origins = [
        "http://localhost:5173", 
        "http://localhost:5174",
        # Known Vercel deployment URLs
        "https://purrfect-spots-mojjn4lys-chalconners-projects.vercel.app", 
        "https://purrfect-spots-qu2kn0dcs-chalconners-projects.vercel.app",
        # Allow all purrfect-spots vercel deployments
        "https://purrfect-spots.vercel.app",
    ]

# Add specific Vercel URL if provided
vercel_url = os.getenv("VERCEL_URL")
if vercel_url:
    allowed_origins.append(f"https://{vercel_url}")

# For development, allow all origins OR for production allow Vercel pattern
is_dev = os.getenv("DEBUG", "False").lower() == "true"
if is_dev:
    print("🚨 Development mode: Allowing all origins")
    allowed_origins = ["*"]

print(f"🌐 CORS allowed origins: {allowed_origins}")

# Custom CORS handler for Vercel pattern matching
def is_vercel_origin_allowed(origin: str) -> bool:
    """Check if origin matches allowed Vercel pattern"""
    import re
    vercel_patterns = [
        r"https://purrfect-spots-[a-zA-Z0-9]+-chalconners-projects\.vercel\.app",
        r"https://purrfect-spots.*\.vercel\.app"
    ]
    for pattern in vercel_patterns:
        if re.match(pattern, origin):
            return True
    return False

# Extend allowed_origins to support Vercel pattern matching
original_allowed_origins = allowed_origins.copy()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if not is_dev else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware to handle dynamic CORS for Vercel
@app.middleware("http")
async def custom_cors_handler(request: Request, call_next):
    origin = request.headers.get("origin")
    
    # If origin is not in static list but matches Vercel pattern, add CORS headers
    if origin and origin not in original_allowed_origins and is_vercel_origin_allowed(origin):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    
    return await call_next(request)

# ✅ Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "PurrFect Spots API is running"}

# ✅ Include routers AFTER middleware
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
def get_locations(supabase = Depends(get_supabase_client)):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)