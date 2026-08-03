"""
Health check routes for Purrfect Spots API

Provides comprehensive health checks for:
- Liveness: Is the application running?
- Readiness: Can the application serve requests?
- Dependency checks: Database, Redis, S3, external APIs

These endpoints are designed for:
- Kubernetes/Container orchestrators
- Load balancer health checks
- Monitoring and alerting systems
"""

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from time import monotonic
from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.app_info import APP_VERSION
from app.config import config
from app.limiter import limiter
from app.logger import logger

ERROR_CONNECTION_FAILED = "Connection failed"
CACHE_CONTROL_NO_STORE = "no-cache, no-store, must-revalidate"

router = APIRouter(prefix="/health", tags=["Health"])
_READINESS_CACHE_TTL_SECONDS = 5.0
_READINESS_CACHE_ENABLED = (
    os.getenv("HEALTH_READINESS_CACHE_ENABLED", "true" if config.is_production() else "false").lower() == "true"
)
_readiness_cache: tuple[float, int, dict[str, Any]] | None = None
_readiness_cache_lock = asyncio.Lock()


def _calc_latency_ms(start_time: datetime) -> float:
    """Calculate elapsed latency in milliseconds."""
    return round((datetime.now(UTC) - start_time).total_seconds() * 1000, 2)


# ========== Dependency Checks ==========


async def check_database() -> dict[str, Any]:
    """
    Check Supabase/PostgreSQL database connectivity (Async).

    Returns:
        Dict with status, latency, and any error message
    """
    start_time = datetime.now(UTC)
    try:
        from app.dependencies import get_async_supabase_client

        supabase = await get_async_supabase_client()
        # Connectivity check only: avoid expensive exact counts on frequently
        # polled readiness endpoints.
        _ = await supabase.table("cat_photos").select("id").limit(1).execute()

        return {
            "status": "healthy",
            "latency_ms": _calc_latency_ms(start_time),
            "connection": "active",
        }
    except Exception as e:
        #         latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
        logger.error("Database health check failed: %s", str(e).replace("\n", " ").replace("\r", " "))
        return {"status": "unhealthy", "error": ERROR_CONNECTION_FAILED}


def check_redis() -> dict[str, Any]:
    """
    Check Redis connectivity for caching and rate limiting.

    Returns:
        Dict with status and connection info
    """
    redis_url = config.REDIS_URL

    if not redis_url:
        return {
            "status": "not_configured",
            "message": "Redis URL not set - using in-memory fallback",
        }

    client: Any | None = None
    try:
        import redis

        start_time = datetime.now(UTC)

        client = redis.from_url(redis_url, socket_connect_timeout=5)
        client.ping()

        # Get Redis info for additional diagnostics
        info = client.info("memory")

        return {
            "status": "healthy",
            "latency_ms": _calc_latency_ms(start_time),
            "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
        }
    except ImportError:
        return {"status": "not_available", "error": "Redis package not installed"}
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        return {"status": "unhealthy", "error": ERROR_CONNECTION_FAILED}
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                logger.debug("Failed to close Redis health-check client", exc_info=True)


def check_s3() -> dict[str, Any]:
    """
    Check AWS S3 connectivity for image storage.

    Returns:
        Dict with status and bucket info
    """
    bucket_name = os.getenv("AWS_S3_BUCKET")

    if not bucket_name:
        return {"status": "not_configured", "message": "AWS_S3_BUCKET not set"}

    try:
        import boto3
        from botocore.config import Config as BotoConfig

        start_time = datetime.now(UTC)
        account_id = os.getenv("AWS_ACCOUNT_ID")

        # Create S3 client with timeout and explicit credentials
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "ap-southeast-2"),
            config=BotoConfig(connect_timeout=5, read_timeout=5),
        )

        # Check if bucket exists and is accessible
        # Using ExpectedBucketOwner to verify bucket ownership if account_id is provided
        head_kwargs = {"Bucket": bucket_name}
        if account_id:
            # ExpectedBucketOwner must be numeric string without dashes
            head_kwargs["ExpectedBucketOwner"] = account_id.replace("-", "")

        s3.head_bucket(**head_kwargs)

        return {
            "status": "healthy",
            "latency_ms": _calc_latency_ms(start_time),
            "bucket": bucket_name,
            "ownership_verified": bool(account_id),
        }
    except ImportError:
        return {"status": "not_available", "error": "boto3 package not installed"}
    except Exception as e:
        logger.error("S3 health check failed: %s", e)
        return {"status": "unhealthy", "error": f"{ERROR_CONNECTION_FAILED}: {str(e)}"}


def check_google_vision() -> dict[str, Any]:
    """
    Check Google Vision API connectivity for cat detection.

    Note: This is a lightweight check - it doesn't make actual API calls
    to avoid quota usage. It only verifies credentials are configured.

    Returns:
        Dict with status and configuration info
    """
    try:
        from pathlib import Path

        service_account_json = os.getenv("GOOGLE_VISION_SERVICE_ACCOUNT")
        if service_account_json:
            try:
                service_account_info = json.loads(service_account_json)
            except (json.JSONDecodeError, TypeError):
                return {
                    "status": "unhealthy",
                    "error": "GOOGLE_VISION_SERVICE_ACCOUNT is not valid JSON",
                }

            required_fields = {"project_id", "private_key", "client_email", "token_uri"}
            if (
                not isinstance(service_account_info, dict)
                or service_account_info.get("type") != "service_account"
                or any(not service_account_info.get(field) for field in required_fields)
            ):
                return {
                    "status": "unhealthy",
                    "error": "GOOGLE_VISION_SERVICE_ACCOUNT is incomplete or not a service account credential",
                }

            return {
                "status": "configured",
                "credentials_type": "service_account_json",
                "note": "Service account JSON configured (API not called to save quota)",
            }

        key_path = os.getenv("GOOGLE_VISION_KEY_PATH", "keys/google_vision.json")

        # Check if credentials file exists
        if Path(key_path).exists():
            return {
                "status": "configured",
                "credentials_path": key_path,
                "note": "Credentials file found (API not called to save quota)",
            }
        # Check for application default credentials
        adc_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if adc_path and Path(adc_path).exists():
            return {
                "status": "configured",
                "credentials_type": "application_default",
                "note": "Using ADC credentials",
            }

        return {
            "status": "not_configured",
            "error": f"Credentials file not found at {key_path}",
        }
    except Exception as e:
        logger.error("Google Vision health check failed: %s", e)
        return {"status": "unknown", "error": "Check failed"}


def check_sentry() -> dict[str, Any]:
    """
    Check Sentry error monitoring configuration.

    Returns:
        Dict with Sentry configuration status
    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        return {
            "status": "not_configured",
            "message": "SENTRY_DSN not set - error monitoring disabled",
        }

    return {
        "status": "configured",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


def _detailed_health_enabled() -> bool:
    """Detailed dependency diagnostics are never public in production."""
    return not config.is_production()


def _safe_check_result(result: Any) -> dict[str, Any]:
    """Safely return result dict or error dict if exception occurred."""
    if isinstance(result, Exception):
        return {"status": "error", "error": str(result)}
    return cast("dict[str, Any]", result)


def _summarize_dependency_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return a safe, minimal dependency summary for public health responses."""
    summary = {"status": result.get("status", "unknown")}
    latency = result.get("latency_ms")
    if isinstance(latency, (int, float)):
        summary["latency_ms"] = latency
    return summary


def _summarize_dependency_results(results: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Redact sensitive dependency diagnostics from public responses."""
    return {name: _summarize_dependency_result(result) for name, result in results.items()}


# ========== Health Endpoints ==========


@router.get("")
@router.get("/")
@limiter.limit("100/minute")
def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "PurrFect Spots API is running",
            "version": APP_VERSION,
        },
        headers={"Cache-Control": CACHE_CONTROL_NO_STORE},
    )


@router.get("/live")
@limiter.limit("100/minute")  # SECURITY: Rate limit health checks to prevent abuse
def liveness_check(request: Request) -> JSONResponse:
    """
    Liveness probe - checks if the application is running.

    This is a lightweight check that should always succeed if the
    application is not deadlocked or crashed.

    Used by: Kubernetes liveness probes, basic monitoring

    Returns:
        200 OK if application is alive
    """
    return JSONResponse(
        content={
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": APP_VERSION,
        },
        headers={"Cache-Control": CACHE_CONTROL_NO_STORE},
    )


@router.get("/ready")
@limiter.limit("50/minute")  # SECURITY: Rate limit readiness checks to prevent abuse
async def readiness_check(request: Request) -> JSONResponse:
    """
    Readiness probe - checks if the application can handle requests.

    This checks critical dependencies (database) and reports on
    optional services (Redis, S3).

    Used by: Kubernetes readiness probes, load balancer health checks

    Returns:
        200 OK if ready to serve requests
        503 Service Unavailable if critical dependencies are down
    """
    global _readiness_cache

    now = monotonic()
    if _READINESS_CACHE_ENABLED and _readiness_cache and now - _readiness_cache[0] < _READINESS_CACHE_TTL_SECONDS:
        _, status_code, content = _readiness_cache
        return JSONResponse(
            status_code=status_code,
            content=content,
            headers={"Cache-Control": CACHE_CONTROL_NO_STORE},
        )

    async with _readiness_cache_lock:
        now = monotonic()
        if _READINESS_CACHE_ENABLED and _readiness_cache and now - _readiness_cache[0] < _READINESS_CACHE_TTL_SECONDS:
            _, status_code, content = _readiness_cache
            return JSONResponse(
                status_code=status_code,
                content=content,
                headers={"Cache-Control": CACHE_CONTROL_NO_STORE},
            )

        # Run all checks in parallel using threads to avoid blocking event loop.
        checks = await asyncio.gather(
            check_database(),
            asyncio.to_thread(check_redis),
            asyncio.to_thread(check_s3),
            asyncio.to_thread(check_sentry),
            return_exceptions=True,
        )

        results: dict[str, dict[str, Any]] = {
            "database": _safe_check_result(checks[0]),
            "redis": _safe_check_result(checks[1]),
            "s3": _safe_check_result(checks[2]),
            "sentry": _safe_check_result(checks[3]),
        }

        # Critical services that must be healthy
        critical_services = ["database"]

        # Check if all critical services are healthy
        all_critical_healthy = all(
            isinstance(results.get(service), dict) and results.get(service, {}).get("status") == "healthy"
            for service in critical_services
        )

        # Overall status
        if all_critical_healthy:
            overall_status = "ready"
            status_code = 200
        else:
            overall_status = "not_ready"
            status_code = 503

        content = (
            {
                "status": overall_status,
                "timestamp": datetime.now(UTC).isoformat(),
                "version": APP_VERSION,
                "environment": os.getenv("ENVIRONMENT", "development"),
                "checks": results,
            }
            if _detailed_health_enabled()
            else {
                "status": overall_status,
                "timestamp": datetime.now(UTC).isoformat(),
                "version": APP_VERSION,
                "checks": _summarize_dependency_results(results),
            }
        )
        if _READINESS_CACHE_ENABLED:
            _readiness_cache = (monotonic(), status_code, content)

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={"Cache-Control": CACHE_CONTROL_NO_STORE},
    )


@router.get("/dependencies")
@limiter.limit("20/minute")  # SECURITY: Rate limit dependency checks to prevent abuse
async def dependency_check(request: Request) -> JSONResponse:
    """
    Detailed dependency health check.

    Checks all external services and provides detailed diagnostics.
    This is more verbose than the readiness check and is intended
    for debugging and monitoring dashboards.

    Returns:
        Detailed status of all dependencies
    """
    # Run all checks including Vision API using threads
    checks = await asyncio.gather(
        check_database(),
        asyncio.to_thread(check_redis),
        asyncio.to_thread(check_s3),
        asyncio.to_thread(check_google_vision),
        asyncio.to_thread(check_sentry),
        return_exceptions=True,
    )

    results = {
        "database": _safe_check_result(checks[0]),
        "redis": _safe_check_result(checks[1]),
        "s3": _safe_check_result(checks[2]),
        "google_vision": _safe_check_result(checks[3]),
        "sentry": _safe_check_result(checks[4]),
    }

    # Calculate overall health score
    statuses = [r.get("status", "unknown") for r in results.values()]
    healthy_count = sum(1 for s in statuses if s in ["healthy", "configured"])
    total_count = len(statuses)

    health_score = round((healthy_count / total_count) * 100) if total_count > 0 else 0

    if _detailed_health_enabled():
        content = {
            "timestamp": datetime.now(UTC).isoformat(),
            "version": APP_VERSION,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "health_score": health_score,
            "health_score_label": f"{healthy_count}/{total_count} services healthy",
            "dependencies": results,
        }
    else:
        content = {
            "timestamp": datetime.now(UTC).isoformat(),
            "version": APP_VERSION,
            "health_score": health_score,
            "health_score_label": f"{healthy_count}/{total_count} services healthy",
            "dependencies": _summarize_dependency_results(results),
        }

    return JSONResponse(content=content, headers={"Cache-Control": CACHE_CONTROL_NO_STORE})


@router.get("/metrics")
@limiter.limit("20/minute")  # SECURITY: Rate limit metrics endpoint to prevent abuse
def metrics(request: Request) -> JSONResponse:
    """
    Basic metrics endpoint for monitoring.

    Returns cache stats and basic service metrics.
    This is a simple alternative for environments without Prometheus.
    """
    from app.utils.cache import get_cache_stats

    cache_stats = get_cache_stats()

    if _detailed_health_enabled():
        content = {
            "timestamp": datetime.now(UTC).isoformat(),
            "cache": cache_stats,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": sys.version.split()[0],
        }
    else:
        content = {
            "timestamp": datetime.now(UTC).isoformat(),
            "cache": {
                "mode": cache_stats.get("mode"),
                "redis_connected": cache_stats.get("redis_connected"),
                "memory_cache_size": cache_stats.get("memory_cache_size"),
            },
        }

    return JSONResponse(
        content=content,
        headers={"Cache-Control": CACHE_CONTROL_NO_STORE},
    )
