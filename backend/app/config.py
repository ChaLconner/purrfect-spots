"""
Application Configuration

Centralized configuration with environment variable validation.
Uses fail-fast approach for required variables in production.
"""

import os
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

from app.logger import logger

# Load .env from backend directory
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
dotenv_override = os.getenv("ENVIRONMENT", "development").lower() not in {"test", "testing"}
if env_path.exists():
    load_dotenv(env_path, override=dotenv_override)
else:
    load_dotenv(override=dotenv_override)


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""

    pass


def normalize_single_line_env(value: str) -> str:
    """
    Normalize single-line environment values copied from dashboards/secret managers.

    This removes wrapping quotes and ASCII control characters such as CR/LF that
    can break HTTP headers or SDK client initialization.
    """
    normalized = value.strip()

    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"'", '"'}:
        normalized = normalized[1:-1].strip()

    return "".join(ch for ch in normalized if ord(ch) >= 0x20 and ord(ch) != 0x7F)


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
        return value.strip()

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
        return value.strip()

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
            return value.strip()

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
    # Auto-detect Vercel environment if not explicitly set
    ENVIRONMENT = os.getenv("ENVIRONMENT") or os.getenv("VERCEL_ENV") or "development"
    DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    # SECURITY: Disable background tasks in serverless environments (Vercel) to avoid port exhaustion
    ENABLE_BACKGROUND_TASKS = (
        os.getenv("ENABLE_BACKGROUND_TASKS", "").lower() in ("true", "1", "yes")
        and not os.getenv("VERCEL")
        and ENVIRONMENT != "production"
    )
    # Stripe webhooks are at-least-once and can be delayed. Reconciliation is
    # enabled by default for long-running production workers, disabled in local
    # development/tests unless explicitly enabled, and never started on Vercel.
    _reconciliation_default = "true" if ENVIRONMENT.lower() == "production" else "false"
    ENABLE_SUBSCRIPTION_RECONCILIATION = (
        os.getenv("ENABLE_SUBSCRIPTION_RECONCILIATION", _reconciliation_default).lower() in ("true", "1", "yes")
        and not os.getenv("VERCEL")
        and ENVIRONMENT.lower() not in {"test", "testing"}
    )
    try:
        SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS = max(
            60, int(os.getenv("SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS", "900"))
        )
    except ValueError:
        logger.warning("Invalid SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS; using 900 seconds")
        SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS = 900

    # Supabase - Use consistent naming with fallbacks for backward compatibility
    SUPABASE_URL = normalize_single_line_env(get_env_with_fallback("SUPABASE_URL"))
    SUPABASE_KEY = normalize_single_line_env(get_env_with_fallback("SUPABASE_KEY", "SUPABASE_ANON_KEY"))
    SUPABASE_SERVICE_KEY = normalize_single_line_env(
        get_required_env("SUPABASE_SERVICE_ROLE_KEY", production_only=True)
    )

    # Database (optional - if not set, services use Supabase client API directly)
    # To enable direct DB access, set DATABASE_URL in .env with:
    # postgresql+asyncpg://postgres:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
    _raw_db_url = os.getenv("DATABASE_URL", "")
    # Ignore the placeholder default that ships in config templates
    DATABASE_URL = _raw_db_url if _raw_db_url and "PASSWORD" not in _raw_db_url else ""

    # Google Auth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # JWT Config - Enforce separate secrets for security
    # BEST PRACTICE: Fail fast if secret is missing. Do not use hardcoded fallbacks in production.
    try:
        JWT_SECRET = get_required_env("JWT_SECRET")
        if (
            ENVIRONMENT.lower() == "production"
            and JWT_SECRET == "purrfect_spots_jwt_secret_key_2025_secure_random_string_change_in_production"
        ):
            raise ConfigurationError(
                "CRITICAL: JWT_SECRET environment variable is using the default development placeholder key in production. "
                "Please change JWT_SECRET in your production settings to a strong 32+ character random string."
            )
    except ConfigurationError:
        if ENVIRONMENT.lower() == "production":
            raise ConfigurationError(
                "CRITICAL: JWT_SECRET environment variable is MISSING. "
                "The application cannot sign authentication tokens safely. "
                "Please add JWT_SECRET to your Vercel Project Settings / Environment Variables. "
                "Generate a strong 32+ character random string."
            )
        JWT_SECRET = "dev-jwt-secret-stable-for-local-testing"

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
            # SECURITY: Use a deterministic fallback for development stability
            # This ensures sessions persist across dev server restarts
            warnings.warn(
                "JWT_REFRESH_SECRET not set. Using a deterministic development secret. "
                "For production, please set a separate JWT_REFRESH_SECRET environment variable.",
                UserWarning,
                stacklevel=2,
            )
            JWT_REFRESH_SECRET = "dev-refresh-secret-do-not-use-in-production-32chars"  # nosec S105

    JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))
    JWT_ACCESS_EXPIRATION_HOURS = int(os.getenv("JWT_ACCESS_EXPIRATION_HOURS", "1"))
    JWT_ALGORITHM = "HS256"

    # Redis (optional)
    REDIS_URL = os.getenv("REDIS_URL", "").replace("localhost", "127.0.0.1")
    # Queue traffic uses a dedicated Redis instance in production so cache
    # eviction cannot discard unprocessed Stripe or Vision jobs.
    QUEUE_REDIS_URL = os.getenv("QUEUE_REDIS_URL", REDIS_URL).replace("localhost", "127.0.0.1")

    # Durable external-work queue controls. The API only enables these paths
    # when a long-lived worker is deployed with the same queue Redis URL.
    ENABLE_STRIPE_WEBHOOK_QUEUE = os.getenv("ENABLE_STRIPE_WEBHOOK_QUEUE", "false").lower() in ("true", "1", "yes")
    ENABLE_VISION_ANALYSIS_QUEUE = os.getenv("ENABLE_VISION_ANALYSIS_QUEUE", "false").lower() in ("true", "1", "yes")
    try:
        QUEUE_MAX_ATTEMPTS = max(1, int(os.getenv("QUEUE_MAX_ATTEMPTS", "5")))
        QUEUE_VISIBILITY_TIMEOUT_SECONDS = max(10, int(os.getenv("QUEUE_VISIBILITY_TIMEOUT_SECONDS", "60")))
        QUEUE_RESULT_TTL_SECONDS = max(60, int(os.getenv("QUEUE_RESULT_TTL_SECONDS", "1800")))
        QUEUE_STREAM_MAXLEN = max(100, int(os.getenv("QUEUE_STREAM_MAXLEN", "10000")))
        VISION_QUEUE_MAX_IMAGE_BYTES = max(
            256 * 1024,
            int(os.getenv("VISION_QUEUE_MAX_IMAGE_BYTES", str(5 * 1024 * 1024))),
        )
    except ValueError:
        logger.warning("Invalid queue configuration; using safe defaults")
        QUEUE_MAX_ATTEMPTS = 5
        QUEUE_VISIBILITY_TIMEOUT_SECONDS = 60
        QUEUE_RESULT_TTL_SECONDS = 1800
        QUEUE_STREAM_MAXLEN = 10000
        VISION_QUEUE_MAX_IMAGE_BYTES = 5 * 1024 * 1024

    # App URLs
    _frontend_urls = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
    FRONTEND_URL = _frontend_urls[0].strip() if _frontend_urls else "http://localhost:5173"

    # Sentry (optional)
    SENTRY_DSN = os.getenv("SENTRY_DSN")

    # AWS configuration
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

    # CDN Configuration
    CDN_BASE_URL = os.getenv("CDN_BASE_URL", "").rstrip("/")

    # Feature Flags
    # Enable external image proxy (wsrv.nl) for non-Supabase images
    # Default: True (to maintain current behavior)
    ENABLE_IMAGE_PROXY = os.getenv("ENABLE_IMAGE_PROXY", "true").lower() in ("true", "1", "yes")

    # ==========================================
    # Upload Configuration
    # ==========================================
    UPLOAD_MAX_SIZE_MB = int(os.getenv("UPLOAD_MAX_SIZE_MB", "10"))
    UPLOAD_MAX_DIMENSION = int(os.getenv("UPLOAD_MAX_DIMENSION", "1920"))
    RATE_LIMIT_UPLOAD_FREE = os.getenv("RATE_LIMIT_UPLOAD_FREE", "5/minute")
    RATE_LIMIT_UPLOAD_PRO = os.getenv("RATE_LIMIT_UPLOAD_PRO", "20/minute")

    # ==========================================
    # Quota Configuration
    # ==========================================
    QUOTA_FREE_LIMIT = int(os.getenv("QUOTA_FREE_LIMIT", "2"))
    QUOTA_PRO_LIMIT = int(os.getenv("QUOTA_PRO_LIMIT", "30"))

    # ==========================================
    # Gallery/Pagination Configuration
    # ==========================================

    # ==========================================
    # Rate Limiting Configuration
    # ==========================================
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")
    RATE_LIMIT_FORGOT_PASSWORD = os.getenv("RATE_LIMIT_FORGOT_PASSWORD", "3/minute")
    RATE_LIMIT_API_DEFAULT = os.getenv("RATE_LIMIT_API_DEFAULT", "60/minute")

    # Tiered API Limits
    RATE_LIMIT_STRICT_FREE = os.getenv("RATE_LIMIT_STRICT_FREE", "10/minute")
    RATE_LIMIT_STRICT_PRO = os.getenv("RATE_LIMIT_STRICT_PRO", "30/minute")
    RATE_LIMIT_API_FREE = os.getenv("RATE_LIMIT_API_FREE", "60/minute")
    RATE_LIMIT_API_PRO = os.getenv("RATE_LIMIT_API_PRO", "300/minute")

    # ==========================================
    # Security Configuration
    # ==========================================
    # ==========================================
    # Payment / Subscription Configuration
    # ==========================================
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID")
    STRIPE_PRO_ANNUAL_PRICE_ID = os.getenv("STRIPE_PRO_ANNUAL_PRICE_ID")

    STRIPE_API_VERSION = "2025-02-24.acacia"

    # Operational controls

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
            ("SUPABASE_SERVICE_ROLE_KEY", Config.SUPABASE_SERVICE_KEY),
        ]

        # Stripe keys are optional; warn if missing since features will be disabled
        stripe_vars = [
            ("STRIPE_SECRET_KEY", Config.STRIPE_SECRET_KEY),
            ("STRIPE_WEBHOOK_SECRET", Config.STRIPE_WEBHOOK_SECRET),
            ("STRIPE_PRO_PRICE_ID", Config.STRIPE_PRO_PRICE_ID),
            ("STRIPE_PRO_ANNUAL_PRICE_ID", Config.STRIPE_PRO_ANNUAL_PRICE_ID),
        ]

        for r_name, r_value in required_vars:
            if not r_value:
                missing.append(r_name)

        # Stripe keys are optional; warn if missing since features will be disabled
        missing_stripe = [s_name for s_name, s_value in stripe_vars if not s_value]
        if missing_stripe:
            logger.info(
                f"Subscription features disabled: Missing optional config {', '.join(missing_stripe)}. "
                "This is expected if you haven't configured Stripe yet."
            )

        return missing

    @staticmethod
    def get_allowed_origins() -> list[str]:
        """
        Get list of allowed CORS origins.

        Returns:
            List of allowed origin URLs
        """

        def normalize_origin(raw_origin: str) -> str | None:
            origin = raw_origin.strip().rstrip("/")
            if not origin or origin == "*":
                return None
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                return None
            if parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
                return None
            return f"{parsed.scheme}://{parsed.netloc}"

        cors_origins_str = os.getenv("CORS_ORIGINS", "").strip()
        environment = os.getenv("ENVIRONMENT", "development").lower()

        if cors_origins_str:
            raw_origins = cors_origins_str.split(",")
        elif environment == "production":
            # Production must opt in to exact frontend origins. Never add
            # localhost or unrelated production domains implicitly.
            raw_origins = [value for value in os.getenv("FRONTEND_URL", "").split(",") if value.strip()]
            vercel_url = os.getenv("VERCEL_URL", "").strip()
            if vercel_url:
                raw_origins.append(vercel_url if "://" in vercel_url else f"https://{vercel_url}")
            if not raw_origins:
                logger.error("No CORS origin configured for production")
        else:
            raw_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]

        allowed: list[str] = []
        for raw_origin in raw_origins:
            origin = normalize_origin(raw_origin)
            if origin and origin not in allowed:
                allowed.append(origin)

        return allowed

    @staticmethod
    def get_trusted_proxy_hosts() -> list[str]:
        """
        Get the proxy IPs/CIDRs allowed to set forwarded headers.

        Wildcard trust is intentionally rejected because it allows any client
        to spoof X-Forwarded-* headers.
        """
        default_hosts = ["127.0.0.1", "::1"]
        raw_hosts = get_env_with_fallback("TRUSTED_PROXY_HOSTS", "TRUSTED_HOSTS")

        if not raw_hosts:
            return default_hosts

        hosts = [host.strip() for host in raw_hosts.split(",") if host.strip()]
        if not hosts or "*" in hosts:
            warnings.warn(
                "Wildcard trusted proxy configuration is unsafe. Falling back to loopback-only trusted proxies.",
                UserWarning,
                stacklevel=2,
            )
            return default_hosts

        return hosts

    @staticmethod
    def get_frontend_origin() -> str:
        """Return the canonical frontend origin without any path component."""
        parsed = urlsplit(Config.FRONTEND_URL)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return Config.FRONTEND_URL.rstrip("/")

    @staticmethod
    def resolve_frontend_url(candidate_url: str | None = None, default_path: str = "/") -> str:
        """
        Build a safe frontend redirect URL.

        Only same-origin absolute URLs or local paths are accepted; everything
        else falls back to the configured frontend URL.
        """
        base_origin = Config.get_frontend_origin()
        safe_path = default_path if default_path.startswith("/") else f"/{default_path}"

        if candidate_url:
            parsed = urlsplit(candidate_url)
            if parsed.scheme and parsed.netloc:
                candidate_origin = f"{parsed.scheme}://{parsed.netloc}"
                if candidate_origin == base_origin:
                    safe_path = parsed.path or "/"
                    if parsed.query:
                        safe_path = f"{safe_path}?{parsed.query}"
            elif candidate_url.startswith("/") and not candidate_url.startswith("//"):
                safe_path = candidate_url

        return f"{base_origin}{safe_path}"

    @staticmethod
    def is_production() -> bool:
        """Check if running in production mode."""
        return Config.ENVIRONMENT.lower() == "production"


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
