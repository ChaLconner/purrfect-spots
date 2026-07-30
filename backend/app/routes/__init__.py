"""
Backend Routes Package

Organized FastAPI route modules and versioned API router:
- api_v1: Aggregated v1 API router (/api/v1)
"""

from app.routes.api_v1 import router as api_v1_router

__all__ = ["api_v1_router"]
