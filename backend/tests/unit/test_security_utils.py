import pytest
from utils.security import (
    sanitize_text, sanitize_html, sanitize_tag, sanitize_tags,
    sanitize_location_name, sanitize_description, is_safe_filename,
    log_security_event, log_audit_event, log_authentication_event,
    log_data_access_event, log_file_operation_event
)
from unittest.mock import patch

def test_sanitize_text():
    assert sanitize_text("  hello  ") == "hello"
    assert sanitize_text("<script>alert(1)</script>hello") == "hello" # bleach isn't used here but re regex strips script tags content
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
    log_security_event("test_event", user_id="u1", details={"k": "v"}, ip_address="1.1", user_agent="agent", severity="WARNING")
    mock_logger.warning.assert_called_once()
    
    mock_logger.reset_mock()
    log_security_event("test_error", severity="ERROR")
    mock_logger.error.assert_called_once()

@patch("utils.security.logger")
def test_log_audit_event(mock_logger):
    log_audit_event("test_action", user_id="u1", resource_type="type", resource_id="r1", details={"k": "v"}, ip_address="1.1", user_agent="agent")
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
    log_file_operation_event("upload", user_id="u1", filename="a.jpg", file_size=100, file_type="image/jpeg", error_message="err")
    mock_audit.assert_called_once()
