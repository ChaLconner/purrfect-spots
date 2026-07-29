"""
Minimal structlog-compatible shim used when the real dependency is unavailable.

The project only relies on a small subset of structlog's API. Providing that
subset locally prevents serverless cold starts from failing if the package is
missing from a preview deployment.
"""

from __future__ import annotations

import logging
from typing import Any

_LOG_KWARGS = {"exc_info", "stack_info", "stacklevel", "extra"}


def _normalize_logger_name(name: str | None) -> str:
    if not name:
        return "purrfect_spots"
    if name.startswith("purrfect_spots"):
        return name
    return f"purrfect_spots.{name}"


def _sanitize_context_value(value: Any) -> str:
    text = repr(value)
    return text.replace("\n", "\\n").replace("\r", "\\r")


class BoundLogger:
    """Small logger wrapper that accepts structlog-style keyword context."""

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None) -> None:
        self._logger = logger
        self._context = context or {}

    def bind(self, **new_values: Any) -> BoundLogger:
        return BoundLogger(self._logger, {**self._context, **new_values})

    def new(self, **new_values: Any) -> BoundLogger:
        return BoundLogger(self._logger, dict(new_values))

    def unbind(self, *keys: str) -> BoundLogger:
        next_context = dict(self._context)
        for key in keys:
            next_context.pop(key, None)
        return BoundLogger(self._logger, next_context)

    def _split_kwargs(self, kwargs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        log_kwargs = {key: value for key, value in kwargs.items() if key in _LOG_KWARGS}
        event_kwargs = {key: value for key, value in kwargs.items() if key not in _LOG_KWARGS}
        return log_kwargs, event_kwargs

    def _render_event(self, event: str, event_kwargs: dict[str, Any]) -> str:
        merged_context = {**self._context, **event_kwargs}
        if not merged_context:
            return event
        rendered = " ".join(f"{key}={_sanitize_context_value(value)}" for key, value in sorted(merged_context.items()))
        return f"{event} | {rendered}"

    def _log(self, level: int, event: Any, *args: Any, **kwargs: Any) -> None:
        log_kwargs, event_kwargs = self._split_kwargs(kwargs)
        message = self._render_event(str(event), event_kwargs)
        self._logger.log(level, message, *args, **log_kwargs)

    def debug(self, event: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, event, *args, **kwargs)

    def info(self, event: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, event, *args, **kwargs)

    def warning(self, event: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, event, *args, **kwargs)

    warn = warning

    def error(self, event: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, event, *args, **kwargs)

    def critical(self, event: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, event, *args, **kwargs)

    def exception(self, event: Any, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("exc_info", True)
        self._log(logging.ERROR, event, *args, **kwargs)

    def msg(self, event: Any, *args: Any, **kwargs: Any) -> None:
        self.info(event, *args, **kwargs)


def get_logger(name: str | None = None, **initial_values: Any) -> BoundLogger:
    """Return a standard-logging-backed logger with a structlog-like surface."""
    return BoundLogger(logging.getLogger(_normalize_logger_name(name)), dict(initial_values))


__all__ = ["BoundLogger", "get_logger"]
