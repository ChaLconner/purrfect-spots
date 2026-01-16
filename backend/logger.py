"""
Centralized Logging Module

Provides:
- Consistent log formatting
- Performance timing utilities
- Request ID tracking
- Structured logging for production
- Color-coded output for development
"""

import json
import logging
import os
import sys
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import wraps
from typing import Any, TypeVar

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for production environments.
    Outputs logs as JSON for easy parsing by log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Color-coded formatter for development environments.
    Makes logs easier to read in terminal.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)

        # Add duration if present
        duration_str = ""
        if hasattr(record, "duration_ms"):
            duration_str = f" [{record.duration_ms:.2f}ms]"

        # Add request ID if present
        request_str = ""
        if hasattr(record, "request_id"):
            request_str = f" [req:{record.request_id[:8]}]"

        formatted = (
            f"{color}%(asctime)s - %(levelname)s{self.RESET}"
            f"{request_str}{duration_str} - "
            f"%(name)s.%(funcName)s:%(lineno)d - %(message)s"
        )

        formatter = logging.Formatter(formatted, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str = "purrfect_spots") -> logging.Logger:
    """
    Setup centralized logger with consistent formatting.

    Uses JSON formatting in production, colored output in development.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level, logging.INFO))

        # Use JSON formatter in production, colored in development
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

        if is_production:
            handler.setFormatter(StructuredFormatter())
        else:
            handler.setFormatter(ColoredFormatter())

        # Add handler to logger
        logger.addHandler(handler)

    return logger


# Create default logger instance
logger = setup_logger()


def log_performance(operation_name: str = None):
    """
    Decorator to log function execution time.

    Args:
        operation_name: Optional custom name for the operation

    Example:
        @log_performance("fetch_gallery_images")
        async def get_images():
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log with extra duration field
                log_record = logging.LogRecord(
                    name="purrfect_spots",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=f"✓ {name} completed",
                    args=(),
                    exc_info=None,
                )
                log_record.duration_ms = duration_ms
                log_record.funcName = func.__name__
                logger.handle(log_record)

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                log_record = logging.LogRecord(
                    name="purrfect_spots",
                    level=logging.ERROR,
                    pathname="",
                    lineno=0,
                    msg=f"✗ {name} failed: {e!s}",
                    args=(),
                    exc_info=None,
                )
                log_record.duration_ms = duration_ms
                log_record.funcName = func.__name__
                logger.handle(log_record)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                log_record = logging.LogRecord(
                    name="purrfect_spots",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=f"✓ {name} completed",
                    args=(),
                    exc_info=None,
                )
                log_record.duration_ms = duration_ms
                log_record.funcName = func.__name__
                logger.handle(log_record)

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                log_record = logging.LogRecord(
                    name="purrfect_spots",
                    level=logging.ERROR,
                    pathname="",
                    lineno=0,
                    msg=f"✗ {name} failed: {e!s}",
                    args=(),
                    exc_info=None,
                )
                log_record.duration_ms = duration_ms
                log_record.funcName = func.__name__
                logger.handle(log_record)
                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


@contextmanager
def log_timing(operation_name: str):
    """
    Context manager for timing code blocks.

    Example:
        with log_timing("process_image"):
            # ... processing code ...
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000

        if duration_ms > 1000:  # Log slow operations (> 1 second)
            logger.warning(f"⚠️ {operation_name} took {duration_ms:.2f}ms (slow)")
        else:
            logger.debug(f"⏱️ {operation_name} took {duration_ms:.2f}ms")


def log_request(request_id: str, method: str, path: str, user_id: str = None):
    """
    Log incoming request with context.

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        user_id: Optional user ID if authenticated
    """
    log_record = logging.LogRecord(
        name="purrfect_spots",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"→ {method} {path}",
        args=(),
        exc_info=None,
    )
    log_record.request_id = request_id
    if user_id:
        log_record.user_id = user_id
    log_record.funcName = "request"
    logger.handle(log_record)


def log_response(request_id: str, status_code: int, duration_ms: float):
    """
    Log outgoing response with timing.

    Args:
        request_id: Unique request identifier
        status_code: HTTP status code
        duration_ms: Request processing duration in milliseconds
    """
    level = (
        logging.INFO
        if status_code < 400
        else logging.WARNING
        if status_code < 500
        else logging.ERROR
    )
    status_emoji = "✓" if status_code < 400 else "⚠️" if status_code < 500 else "✗"

    log_record = logging.LogRecord(
        name="purrfect_spots",
        level=level,
        pathname="",
        lineno=0,
        msg=f"← {status_emoji} {status_code}",
        args=(),
        exc_info=None,
    )
    log_record.request_id = request_id
    log_record.duration_ms = duration_ms
    log_record.funcName = "response"
    logger.handle(log_record)
