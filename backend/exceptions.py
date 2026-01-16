"""
Custom exception classes for Purrfect Spots API

Provides standardized exception handling with:
- Consistent error response format
- Error codes for client-side handling
- Proper HTTP status codes
"""

from typing import Any


class PurrfectSpotsException(Exception):
    """
    Base exception for all application-specific errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for the response
        error_code: Machine-readable error code for client handling
        details: Optional additional error details
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        response = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            response["details"] = self.details
        return response


class ValidationError(PurrfectSpotsException):
    """
    Raised when input validation fails.

    Args:
        message: Description of the validation error
        field: Optional field name that failed validation
        value: Optional invalid value (sanitized)
    """

    def __init__(
        self, message: str, field: str | None = None, value: str | None = None
    ):
        details = {}
        if field:
            details["field"] = field
        if value:
            details["value"] = value

        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )
        self.field = field


class AuthenticationError(PurrfectSpotsException):
    """
    Raised when authentication fails.

    Args:
        message: Description of the authentication error
        reason: Specific reason code (e.g., "invalid_token", "expired")
    """

    def __init__(
        self, message: str = "Authentication required", reason: str | None = None
    ):
        details = {"reason": reason} if reason else {}
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )
        self.reason = reason


class AuthorizationError(PurrfectSpotsException):
    """
    Raised when user lacks permission for an action.

    Args:
        message: Description of what was denied
        resource: Optional resource that was being accessed
    """

    def __init__(
        self, message: str = "Permission denied", resource: str | None = None
    ):
        details = {"resource": resource} if resource else {}
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )
        self.resource = resource


class RateLimitError(PurrfectSpotsException):
    """
    Raised when rate limit is exceeded.

    Args:
        message: Description of the rate limit
        retry_after: Seconds until rate limit resets
    """

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )
        self.retry_after = retry_after


class NotFoundError(PurrfectSpotsException):
    """
    Raised when a requested resource is not found.

    Args:
        message: Description of what was not found
        resource_type: Type of resource (e.g., "photo", "user")
        resource_id: ID of the missing resource
    """

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message, status_code=404, error_code="NOT_FOUND", details=details
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictError(PurrfectSpotsException):
    """
    Raised when there's a conflict with existing data.

    Args:
        message: Description of the conflict
        conflicting_field: Field that caused the conflict
    """

    def __init__(
        self,
        message: str = "Resource already exists",
        conflicting_field: str | None = None,
    ):
        details = {"field": conflicting_field} if conflicting_field else {}
        super().__init__(
            message=message, status_code=409, error_code="CONFLICT", details=details
        )
        self.conflicting_field = conflicting_field


class ExternalServiceError(PurrfectSpotsException):
    """
    Raised when an external service (S3, Vision API, etc.) fails.

    Args:
        message: Description of the failure
        service: Name of the external service
        retryable: Whether the operation can be retried
    """

    def __init__(
        self,
        message: str = "External service error",
        service: str | None = None,
        retryable: bool = False,
    ):
        details = {"service": service, "retryable": retryable}
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )
        self.service = service
        self.retryable = retryable


class FileProcessingError(PurrfectSpotsException):
    """
    Raised when file processing fails.

    Args:
        message: Description of the processing error
        filename: Name of the file that failed
        reason: Specific reason for failure
    """

    def __init__(
        self,
        message: str = "File processing failed",
        filename: str | None = None,
        reason: str | None = None,
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            status_code=400,
            error_code="FILE_PROCESSING_ERROR",
            details=details,
        )
        self.filename = filename
        self.reason = reason


class CatDetectionError(PurrfectSpotsException):
    """
    Raised when cat detection fails or no cat is detected.

    Args:
        message: Description of the detection issue
        confidence: Confidence score if available
    """

    def __init__(
        self, message: str = "Cat detection failed", confidence: float | None = None
    ):
        details = {"confidence": confidence} if confidence is not None else {}
        super().__init__(
            message=message,
            status_code=400,
            error_code="CAT_DETECTION_FAILED",
            details=details,
        )
        self.confidence = confidence
