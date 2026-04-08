from unittest.mock import patch

from utils.security import (
    is_safe_filename,
    log_audit_event,
    log_authentication_event,
    log_data_access_event,
    log_file_operation_event,
    log_security_event,
    protect_public_coordinates,
    sanitize_description,
    sanitize_html,
    sanitize_location_name,
    sanitize_tag,
    sanitize_tags,
    sanitize_text,
    validate_content_type_matches,
    validate_image_magic_bytes,
)


def test_sanitize_text():
    assert sanitize_text("  hello  ") == "hello"
    assert (
        sanitize_text("<script>alert(1)</script>hello") == "hello"
    )  # bleach isn't used here but re regex strips script tags content
    assert sanitize_text("test", max_length=2) == "te"
    assert sanitize_text("") == ""


def test_sanitize_html():
    html = "<b>hello</b> <script>bad</script>"
    assert sanitize_html(html) == "hello bad"
    assert sanitize_html(html, allowed_tags=["b"]) == "<b>hello</b> bad"


def test_sanitize_tag():
    assert sanitize_tag("#Hello_World 123!") == "hello_world 123"
    assert sanitize_tag("") == ""


def test_sanitize_tags():
    assert sanitize_tags(["#A", "b!", " a ", ""]) == ["a", "b"]
    assert sanitize_tags(None) == []


def test_sanitize_location_name():
    assert sanitize_location_name("  Test Location  ") == "Test Location"


def test_sanitize_description():
    assert sanitize_description("  Test Desc  ") == "Test Desc"


def test_is_safe_filename():
    assert is_safe_filename("test.jpg") is True
    assert is_safe_filename("../test.jpg") is False
    assert is_safe_filename("test/test.jpg") is False
    assert is_safe_filename(r"test\test.jpg") is False
    assert is_safe_filename("test\x00.jpg") is False
    assert is_safe_filename("") is False
    assert is_safe_filename("a" * 300 + ".jpg") is False


@patch("utils.security.logger")
def test_log_security_event(mock_logger):
    log_security_event(
        "test_event", user_id="u1", details={"k": "v"}, ip_address="1.1", user_agent="agent", severity="WARNING"
    )
    mock_logger.warning.assert_called_once()

    mock_logger.reset_mock()
    log_security_event("test_error", severity="ERROR")
    mock_logger.error.assert_called_once()


@patch("utils.security.logger")
def test_log_audit_event(mock_logger):
    log_audit_event(
        "test_action",
        user_id="u1",
        resource_type="type",
        resource_id="r1",
        details={"k": "v"},
        ip_address="1.1",
        user_agent="agent",
    )
    mock_logger.info.assert_called_once()

    mock_logger.reset_mock()
    log_audit_event("fail_action", success=False)
    mock_logger.warning.assert_called_once()


@patch("utils.security.log_audit_event")
def test_log_authentication_event(mock_audit):
    log_authentication_event("login", user_id="u1", email="test@example.com", failure_reason="bad")
    mock_audit.assert_called_once()


@patch("utils.security.log_audit_event")
def test_log_data_access_event(mock_audit):
    log_data_access_event("read", user_id="u1", resource_type="photo", resource_id="p1")
    mock_audit.assert_called_once()


@patch("utils.security.log_audit_event")
def test_log_file_operation_event(mock_audit):
    log_file_operation_event(
        "upload", user_id="u1", filename="a.jpg", file_size=100, file_type="image/jpeg", error_message="err"
    )
    mock_audit.assert_called_once()
    args, kwargs = mock_audit.call_args
    assert kwargs["details"]["filename"] == "a.jpg"
    assert kwargs["details"]["file_size"] == 100
    assert kwargs["details"]["file_type"] == "image/jpeg"
    assert kwargs["details"]["error"] == "err"


def test_validate_image_magic_bytes():
    """Test image magic bytes validation"""
    # JPEG magic bytes
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    is_valid, mime, error = validate_image_magic_bytes(jpeg_bytes)
    assert is_valid is True
    assert mime == "image/jpeg"

    # Empty file
    is_valid, mime, error = validate_image_magic_bytes(b"")
    assert is_valid is False
    assert error == "Empty file content"

    # Invalid type
    is_valid, mime, error = validate_image_magic_bytes(b"plain text file")
    assert is_valid is False
    assert "not allowed" in error


def test_validate_content_type_matches():
    """Test matching claimed content type with detected type"""
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"

    # Matching
    is_match, mime = validate_content_type_matches("image/jpeg", jpeg_bytes)
    assert is_match is True

    # Alias matching
    is_match, mime = validate_content_type_matches("image/jpg", jpeg_bytes)
    assert is_match is True

    # Mismatch
    is_match, mime = validate_content_type_matches("image/png", jpeg_bytes)
    assert is_match is False


def test_protect_public_coordinates():
    lat, lng = 13.7563, 100.5018
    p_lat, p_lng = protect_public_coordinates(lat, lng)

    # Should be rounded but close
    assert round(p_lat, 2) == round(lat, 2)
    assert round(p_lng, 2) == round(lng, 2)

    # Should be deterministic with same seed
    p_lat2, p_lng2 = protect_public_coordinates(lat, lng, seed="test-seed")
    p_lat3, p_lng3 = protect_public_coordinates(lat, lng, seed="test-seed")
    assert p_lat2 == p_lat3
    assert p_lng2 == p_lng3
