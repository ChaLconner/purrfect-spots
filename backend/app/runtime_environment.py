"""Runtime environment resolution shared by configuration and middleware."""

import os


def resolve_environment() -> str:
    """Return the normalized deployment environment.

    ``ENVIRONMENT`` is the explicit application override. ``VERCEL_ENV`` is
    the platform-provided fallback because Vercel does not provide an
    automatic ``ENVIRONMENT`` variable.
    """

    return (os.getenv("ENVIRONMENT") or os.getenv("VERCEL_ENV") or "development").strip().lower()


def is_production_environment() -> bool:
    """Return whether the current process is running in production."""

    return resolve_environment() == "production"
