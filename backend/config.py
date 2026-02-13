"""
Application Configuration

Centralized configuration with environment variable validation.
Uses fail-fast approach for required variables in production.
"""

import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend directory
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""

    pass


def get_required_env(key: str, production_only: bool = False) -> str:
    """
    Get a required environment variable.

    Args:
        key: Environment variable name
        production_only: If True, only required in production mode

    Returns:
        The environment variable value

    Raises:
        ConfigurationError: If the variable is missing when required
    """
    value = os.getenv(key)
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

    if value:
        return value

    if production_only and not is_production:
        return ""

    if is_production:
        raise ConfigurationError(
            f"Required environment variable '{key}' is not set. "
            f"Please check your .env file or environment configuration."
        )

    return ""


def get_env_with_fallback(primary_key: str, *fallback_keys: str, default: str = "") -> str:
    """
    Get an environment variable with fallback keys for backward compatibility.

    Args:
        primary_key: The primary environment variable name
        *fallback_keys: Alternative keys to try if primary is not set
        default: Default value if none of the keys are set

    Returns:
        The environment variable value or default
    """
    value = os.getenv(primary_key)
    if value:
        return value

    for key in fallback_keys:
        value = os.getenv(key)
        if value:
            # Log deprecation warning in development
            if os.getenv("ENVIRONMENT", "development").lower() == "development":
                warnings.warn(
                    f"Using deprecated env var '{key}'. Please use '{primary_key}' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            return value

    return default


class Config:
    """
    Application configuration class.

    Environment Variables:
        Required (Production):
            - SUPABASE_URL: Supabase project URL
            - SUPABASE_KEY: Supabase anon key
            - SUPABASE_SERVICE_ROLE_KEY: Supabase service role key
            - JWT_SECRET: Secret key for JWT signing
            - GOOGLE_CLIENT_ID: Google OAuth client ID

        Optional:
            - CORS_ORIGINS: Comma-separated list of allowed origins
            - JWT_REFRESH_SECRET: Separate secret for refresh tokens
            - JWT_REFRESH_EXPIRATION_DAYS: Refresh token expiration (default: 7)
            - REDIS_URL: Redis URL for rate limiting
            - SENTRY_DSN: Sentry DSN for error monitoring
    """

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")

    # Supabase - Use consistent naming with fallbacks for backward compatibility
    SUPABASE_URL = get_env_with_fallback("SUPABASE_URL")
    SUPABASE_KEY = get_env_with_fallback("SUPABASE_KEY", "SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = get_env_with_fallback(
        "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY", "SUPABASE_SECRET_KEY"
    )

    # Google Auth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # JWT Config - Enforce separate secrets for security
    # BEST PRACTICE: Fail fast if secret is missing. Do not use hardcoded fallbacks in production.
    try:
        JWT_SECRET = get_required_env("JWT_SECRET")
    except ConfigurationError:
        raise ConfigurationError(
            "JWT_SECRET is missing! Please add this environment variable in your Vercel Project Settings."
        )

    # JWT_REFRESH_SECRET is REQUIRED in production for security
    # Using the same secret for both access and refresh tokens is a security vulnerability
    JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")

    if not JWT_REFRESH_SECRET:
        if ENVIRONMENT.lower() == "production":
            raise ConfigurationError(
                "JWT_REFRESH_SECRET is required in production! Using the same secret for both access and refresh tokens is a security vulnerability. "
                "Please set JWT_REFRESH_SECRET environment variable."
            )
        else:
            warnings.warn(
                "JWT_REFRESH_SECRET not set. Using JWT_SECRET (NOT SAFE FOR PRODUCTION). "
                "For development, this is acceptable but you should set a separate JWT_REFRESH_SECRET.",
                UserWarning,
                stacklevel=2,
            )
            JWT_REFRESH_SECRET = JWT_SECRET

    JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))
    JWT_ACCESS_EXPIRATION_HOURS = int(os.getenv("JWT_ACCESS_EXPIRATION_HOURS", "1"))
    JWT_ALGORITHM = "HS256"

    # Redis (optional)
    REDIS_URL = os.getenv("REDIS_URL")

    # App URLs
    # App URLs
    _frontend_urls = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
    FRONTEND_URL = _frontend_urls[0].strip() if _frontend_urls else "http://localhost:5173"

    # Sentry (optional)
    SENTRY_DSN = os.getenv("SENTRY_DSN")

    # CDN Configuration
    CDN_BASE_URL = os.getenv("CDN_BASE_URL", "").rstrip("/")

    # ==========================================
    # Upload Configuration
    # ==========================================
    UPLOAD_MAX_SIZE_MB = int(os.getenv("UPLOAD_MAX_SIZE_MB", "10"))
    UPLOAD_MAX_DIMENSION = int(os.getenv("UPLOAD_MAX_DIMENSION", "1920"))
    UPLOAD_ALLOWED_EXTENSIONS = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,webp").split(",")
    UPLOAD_RATE_LIMIT = os.getenv("UPLOAD_RATE_LIMIT", "5/minute")

    # ==========================================
    # Gallery/Pagination Configuration
    # ==========================================
    GALLERY_PAGE_SIZE = int(os.getenv("GALLERY_PAGE_SIZE", "20"))
    GALLERY_MAX_PAGE_SIZE = int(os.getenv("GALLERY_MAX_PAGE_SIZE", "100"))

    # ==========================================
    # Rate Limiting Configuration
    # ==========================================
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")
    RATE_LIMIT_FORGOT_PASSWORD = os.getenv("RATE_LIMIT_FORGOT_PASSWORD", "3/minute")
    RATE_LIMIT_API_DEFAULT = os.getenv("RATE_LIMIT_API_DEFAULT", "60/minute")

    # ==========================================
    # Security Configuration
    # ==========================================
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "").lower() in ("true", "1", "yes") or ENVIRONMENT == "production"
    )
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "lax")

    # ==========================================
    # Session Timeout Configuration
    # ==========================================
    # SECURITY: Define clear session timeout and idle timeout
    # Session timeout: Maximum time a session can be active (absolute)
    # Idle timeout: Maximum time of inactivity before session expires
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "1440"))  # 24 hours default
    SESSION_IDLE_TIMEOUT_MINUTES = int(os.getenv("SESSION_IDLE_TIMEOUT_MINUTES", "30"))  # 30 minutes default
    # Note: JWT_ACCESS_EXPIRATION_HOURS (1 hour) is the actual token expiration
    # SESSION_TIMEOUT_MINUTES and SESSION_IDLE_TIMEOUT_MINUTES are used for:
    # 1. Server-side session tracking (if implemented)
    # 2. Concurrent session management
    # 3. Security event logging
    # 4. User experience (auto-logout on idle)

    # ==========================================
    # Payment / Subscription Configuration
    # ==========================================
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Treat packages are now managed in the database (public.treat_packages)
    # Use TreatsService.get_packages() to fetch them.

    @staticmethod
    def validate_required_config() -> list[str]:
        """
        Validate that all required configuration is present.

        Returns:
            List of missing configuration keys (empty if all required config is present)
        """
        missing = []
        required_vars = [
            ("SUPABASE_URL", Config.SUPABASE_URL),
            ("SUPABASE_KEY", Config.SUPABASE_KEY),
        ]

        for name, value in required_vars:
            if not value:
                missing.append(name)

        return missing

    @staticmethod
    def get_allowed_origins() -> list[str]:
        """
        Get list of allowed CORS origins.

        Returns:
            List of allowed origin URLs
        """
        cors_origins_str = os.getenv("CORS_ORIGINS", "")

        if cors_origins_str:
            allowed = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
        else:
            # Default development origins
            allowed = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "https://purrfect-spots.vercel.app",  # Production Frontend
                "https://purrfectspots.xyz",
                "https://www.purrfectspots.xyz",
            ]

        # Add Vercel URL if present
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            allowed.append(f"https://{vercel_url}")

        # Add frontend URL if present and not already in list
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url and frontend_url not in allowed:
            allowed.append(frontend_url)

        # Force add production frontend URL (Hardcoded safety net)
        prod_urls = [
            "https://purrfect-spots.vercel.app",
            "https://purrfectspots.xyz",
            "https://www.purrfectspots.xyz"
        ]
        for url in prod_urls:
            if url not in allowed:
                allowed.append(url)

        return list(set(allowed))

    @staticmethod
    def get_redirect_uris() -> list[str]:
        """
        Get list of allowed OAuth redirect URIs.

        Returns:
            List of redirect URIs for OAuth callbacks
        """
        allowed_origins = Config.get_allowed_origins()
        return [f"{origin.rstrip('/')}/auth/callback" for origin in allowed_origins]

    @staticmethod
    def is_production() -> bool:
        """Check if running in production mode."""
        return Config.ENVIRONMENT.lower() == "production"

    @staticmethod
    def is_development() -> bool:
        """Check if running in development mode."""
        return Config.ENVIRONMENT.lower() == "development"


# Create singleton instance
config = Config()

# Validate configuration on import (warn in development, error in production)
_missing = config.validate_required_config()
if _missing:
    if config.is_production():
        raise ConfigurationError(
            f"Missing required configuration: {', '.join(_missing)}. Please check your environment variables."
        )
    else:
        warnings.warn(f"Missing recommended configuration: {', '.join(_missing)}", UserWarning, stacklevel=2)
