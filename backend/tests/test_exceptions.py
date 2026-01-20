import pytest

from exceptions import (
    AuthenticationError,
    AuthorizationError,
    CatDetectionError,
    ConflictError,
    ExternalServiceError,
    FileProcessingError,
    NotFoundError,
    PurrfectSpotsException,
    RateLimitError,
    ValidationError,
)


def test_base_exception():
    exc = PurrfectSpotsException("Something wrong", status_code=501, error_code="TEST_ERROR", details={"foo": "bar"})
    assert exc.message == "Something wrong"
    assert exc.status_code == 501
    assert exc.error_code == "TEST_ERROR"
    assert exc.details == {"foo": "bar"}
    
    data = exc.to_dict()
    assert data["error"] is True
    assert data["error_code"] == "TEST_ERROR"
    assert data["message"] == "Something wrong"
    assert data["details"] == {"foo": "bar"}

def test_base_exception_defaults():
    exc = PurrfectSpotsException("Something wrong")
    assert exc.status_code == 500
    assert exc.error_code == "INTERNAL_ERROR"
    assert exc.details == {}
    
    data = exc.to_dict()
    assert "details" not in data

def test_validation_error():
    exc = ValidationError("Invalid input", field="username", value="bob")
    assert exc.status_code == 422
    assert exc.error_code == "VALIDATION_ERROR"
    assert exc.field == "username"
    assert exc.details["field"] == "username"
    assert exc.details["value"] == "bob"

def test_authentication_error():
    exc = AuthenticationError("Auth failed", reason="expired")
    assert exc.status_code == 401
    assert exc.error_code == "AUTHENTICATION_ERROR"
    assert exc.reason == "expired"
    assert exc.details["reason"] == "expired"

def test_authorization_error():
    exc = AuthorizationError("Access denied", resource="admin_panel")
    assert exc.status_code == 403
    assert exc.error_code == "AUTHORIZATION_ERROR"
    assert exc.resource == "admin_panel"
    assert exc.details["resource"] == "admin_panel"

def test_rate_limit_error():
    exc = RateLimitError("Too many requests", retry_after=60)
    assert exc.status_code == 429
    assert exc.error_code == "RATE_LIMIT_EXCEEDED"
    assert exc.retry_after == 60
    assert exc.details["retry_after"] == 60

def test_not_found_error():
    exc = NotFoundError("Missing", resource_type="user", resource_id="123")
    assert exc.status_code == 404
    assert exc.error_code == "NOT_FOUND"
    assert exc.resource_type == "user"
    assert exc.resource_id == "123"
    assert exc.details["resource_type"] == "user"
    assert exc.details["resource_id"] == "123"

def test_conflict_error():
    exc = ConflictError("Duplicate", conflicting_field="email")
    assert exc.status_code == 409
    assert exc.error_code == "CONFLICT"
    assert exc.conflicting_field == "email"
    assert exc.details["field"] == "email"

def test_external_service_error():
    exc = ExternalServiceError("S3 down", service="S3", retryable=True)
    assert exc.status_code == 502
    assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
    assert exc.service == "S3"
    assert exc.retryable is True
    assert exc.details["service"] == "S3"
    assert exc.details["retryable"] is True

def test_file_processing_error():
    exc = FileProcessingError("Corrupt", filename="cat.jpg", reason="header")
    assert exc.status_code == 400
    assert exc.error_code == "FILE_PROCESSING_ERROR"
    assert exc.filename == "cat.jpg"
    assert exc.reason == "header"
    assert exc.details["filename"] == "cat.jpg"
    assert exc.details["reason"] == "header"

def test_cat_detection_error():
    exc = CatDetectionError("No cat", confidence=0.1)
    assert exc.status_code == 400
    assert exc.error_code == "CAT_DETECTION_FAILED"
    assert exc.confidence == 0.1
    assert exc.details["confidence"] == 0.1
