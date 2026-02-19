"""
API v1 Router - Versioned API endpoints

This module aggregates all v1 API routes under /api/v1 prefix.
New versions can be created by adding new router files (api_v2.py, etc.)
"""

from fastapi import APIRouter

# Import all route modules
from routes import (
    auth,
    cat_detection,
    feature_flags,
    gallery,
    notifications,
    profile,
    reports,
    seo,
    social,
    subscription,
    treats,
    upload,
)

# Create versioned router
router = APIRouter(prefix="/api/v1")

# Include all routes with their respective prefixes
# Authentication routes
router.include_router(auth.router)

# User management
router.include_router(profile.router)

# Core features
router.include_router(upload.router)
router.include_router(cat_detection.router)
router.include_router(gallery.router)

# System
router.include_router(feature_flags.router)

# Monetization
router.include_router(subscription.router)
router.include_router(treats.router)

# Social
router.include_router(social.router)
router.include_router(notifications.router)

# SEO
router.include_router(seo.router)

# Reports
router.include_router(reports.router)
