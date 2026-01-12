"""
Environment utilities for Purrfect Spots
Provides helper functions for environment detection
"""
import os


def is_dev() -> bool:
    """Check if running in development mode."""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.getenv(key, default)
