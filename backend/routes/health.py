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
import os
import sys
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import config
from logger import logger

router = APIRouter(prefix="/health", tags=["Health"])


# ========== Dependency Checks ==========


async def check_database() -> dict[str, Any]:
    """
    Check Supabase/PostgreSQL database connectivity.

    Returns:
        Dict with status, latency, and any error message
    """
    start_time = datetime.now(UTC)
    try:
        from dependencies import get_supabase_client

        client = get_supabase_client()

        # Simple query to verify connection - count users (lightweight)
        result = client.table("users").select("id", count="exact").limit(1).execute()

        latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "connection": "active",
        }
    except Exception as e:
        latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 2),
            "error": "Connection failed",
        }


async def check_redis() -> dict[str, Any]:
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

    try:
        import redis

        start_time = datetime.now(UTC)

        client = redis.from_url(redis_url, socket_connect_timeout=5)
        client.ping()

        # Get Redis info for additional diagnostics
        info = client.info("memory")

        latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
        }
    except ImportError:
        return {"status": "not_available", "error": "Redis package not installed"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": "Connection failed"}


async def check_s3() -> dict[str, Any]:
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

        # Create S3 client with timeout
        s3 = boto3.client("s3", config=BotoConfig(connect_timeout=5, read_timeout=5))

        # Check if bucket exists and is accessible
        s3.head_bucket(Bucket=bucket_name)

        latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "bucket": bucket_name,
        }
    except ImportError:
        return {"status": "not_available", "error": "boto3 package not installed"}
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        return {"status": "unhealthy", "error": "Connection failed"}


async def check_google_vision() -> dict[str, Any]:
    """
    Check Google Vision API connectivity for cat detection.

    Note: This is a lightweight check - it doesn't make actual API calls
    to avoid quota usage. It only verifies credentials are configured.

    Returns:
        Dict with status and configuration info
    """
    key_path = os.getenv("GOOGLE_VISION_KEY_PATH", "keys/google_vision.json")

    try:
        from pathlib import Path

        # Check if credentials file exists
        if Path(key_path).exists():
            return {
                "status": "configured",
                "credentials_path": key_path,
                "note": "Credentials file found (API not called to save quota)",
            }
        else:
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
        logger.error(f"Google Vision health check failed: {e}")
        return {"status": "unknown", "error": "Check failed"}


async def check_sentry() -> dict[str, Any]:
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


# ========== Health Endpoints ==========


@router.get("/live")
async def liveness_check():
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
            "version": "3.0.0",
        },
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe - checks if the application can handle requests.

    This checks critical dependencies (database) and reports on
    optional services (Redis, S3).

    Used by: Kubernetes readiness probes, load balancer health checks

    Returns:
        200 OK if ready to serve requests
        503 Service Unavailable if critical dependencies are down
    """
    # Run all checks in parallel
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_s3(),
        check_sentry(),
        return_exceptions=True,
    )

    results = {
        "database": checks[0] if not isinstance(checks[0], Exception) else {"status": "error", "error": str(checks[0])},
        "redis": checks[1] if not isinstance(checks[1], Exception) else {"status": "error", "error": str(checks[1])},
        "s3": checks[2] if not isinstance(checks[2], Exception) else {"status": "error", "error": str(checks[2])},
        "sentry": checks[3] if not isinstance(checks[3], Exception) else {"status": "error", "error": str(checks[3])},
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

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "3.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "checks": results,
        },
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/dependencies")
async def dependency_check():
    """
    Detailed dependency health check.

    Checks all external services and provides detailed diagnostics.
    This is more verbose than the readiness check and is intended
    for debugging and monitoring dashboards.

    Returns:
        Detailed status of all dependencies
    """
    # Run all checks including Vision API
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_s3(),
        check_google_vision(),
        check_sentry(),
        return_exceptions=True,
    )

    def safe_result(result):
        if isinstance(result, Exception):
            return {"status": "error", "error": str(result)}
        return result

    results = {
        "database": safe_result(checks[0]),
        "redis": safe_result(checks[1]),
        "s3": safe_result(checks[2]),
        "google_vision": safe_result(checks[3]),
        "sentry": safe_result(checks[4]),
    }

    # Calculate overall health score
    statuses = [r.get("status", "unknown") for r in results.values()]
    healthy_count = sum(1 for s in statuses if s in ["healthy", "configured"])
    total_count = len(statuses)

    health_score = round((healthy_count / total_count) * 100) if total_count > 0 else 0

    return JSONResponse(
        content={
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "3.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "health_score": health_score,
            "health_score_label": f"{healthy_count}/{total_count} services healthy",
            "dependencies": results,
        },
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/metrics")
async def metrics():
    """
    Basic metrics endpoint for monitoring.

    Returns cache stats and basic service metrics.
    This is a simple alternative for environments without Prometheus.
    """
    from utils.cache import get_cache_stats

    cache_stats = get_cache_stats()

    return JSONResponse(
        content={
            "timestamp": datetime.now(UTC).isoformat(),
            "cache": cache_stats,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": sys.version.split()[0],
        },
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )
