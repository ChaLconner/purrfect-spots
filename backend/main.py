"""Vercel-compatible ASGI entrypoint for the PurrFect Spots API."""

from app.main import app

__all__ = ["app"]
