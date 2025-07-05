"""
Purrfect Spots FastAPI Backend
Main application file
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routes import router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    create_tables()
    logger.info("Database tables created successfully")
    yield
    # Shutdown
    logger.info("Application shutdown")

# Create FastAPI app
app = FastAPI(
    title="Purrfect Spots API",
    description="API for managing cat photos and locations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Purrfect Spots API is running!"}

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    import datetime as dt
    return {"status": "healthy", "timestamp": dt.datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
