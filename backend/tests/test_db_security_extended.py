
import pytest

from utils import db_security


class TestDBSecurityExtended:
    """Extended test suite for DB Security Utils"""

    # ==============================================================================
    # SQL Injection Detection Tests
    # ==============================================================================
    
    @pytest.mark.parametrize("payload", [
        "DROP TABLE users; --",
        "admin' OR '1'='1",
        "UNION SELECT 1, 2, 3",
        "EXEC sp_executesql",
        "char(113)",
        "0x504B0304"
    ])
    def test_detect_sql_injection_positive(self, payload):
        """Test detection of malicious payloads"""
        assert db_security.detect_sql_injection(payload) is True

    @pytest.mark.parametrize("payload", [
        "regular_text",
        "hello world",
        "user_id",
        "12345",
        "my-email@example.com"
    ])
    def test_detect_sql_injection_negative(self, payload):
        """Test that safe payloads are not flagged"""
        assert db_security.detect_sql_injection(payload) is False

    # ==============================================================================
    # Identifier Validation Tests
    # ==============================================================================

    def test_is_safe_identifier_valid(self):
        assert db_security.is_safe_identifier("users") is True
        assert db_security.is_safe_identifier("user_data") is True
        assert db_security.is_safe_identifier("column1") is True
        assert db_security.is_safe_identifier("_hidden") is True

    def test_is_safe_identifier_invalid(self):
        assert db_security.is_safe_identifier("users; DROP TABLE") is False
        assert db_security.is_safe_identifier("user-data") is False  # No hyphens allowed in safe identifier regex
        assert db_security.is_safe_identifier("123user") is False    # Cannot start with number
        assert db_security.is_safe_identifier("") is False
        assert db_security.is_safe_identifier("a" * 129) is False    # Too long

    # ==============================================================================
    # Order By Tests
    # ==============================================================================

    def test_sanitize_order_by(self):
        allowed = ["name", "created_at"]
        
        # Valid cases
        assert db_security.sanitize_order_by("name", allowed) == "name"
        assert db_security.sanitize_order_by("-created_at", allowed) == "created_at DESC"
        
        # Invalid cases
        assert db_security.sanitize_order_by("invalid", allowed, default="name") == "name"
        assert db_security.sanitize_order_by("DROP TABLE", allowed, default="name") == "name"
        assert db_security.sanitize_order_by(None, allowed, default="name") == "name"

    # ==============================================================================
    # Search Input Sanitization Tests
    # ==============================================================================

    def test_sanitize_search_input(self):
        # Basic sanitization
        assert db_security.sanitize_search_input("  hello   world  ") == "hello world"
        
        # Dangerous chars removal
        assert db_security.sanitize_search_input("hello; drop table") == "hello drop table"
        assert db_security.sanitize_search_input("o'reilly") == "oreilly"
        
        # Max length
        long_str = "a" * 200
        result = db_security.sanitize_search_input(long_str, max_length=10)
        assert len(result) == 10

    # ==============================================================================
    # LIKE Pattern Tests
    # ==============================================================================

    def test_escape_like_pattern(self):
        assert db_security.escape_like_pattern("100%") == "100\\%"
        assert db_security.escape_like_pattern("user_name") == "user\\_name"
        assert db_security.escape_like_pattern("C:\\Path") == "C:\\\\Path"

    def test_build_safe_like_pattern(self):
        term = "test_user"
        
        assert db_security.build_safe_like_pattern(term, "contains") == "%test\\_user%"
        assert db_security.build_safe_like_pattern(term, "starts") == "test\\_user%"
        assert db_security.build_safe_like_pattern(term, "ends") == "%test\\_user"
        assert db_security.build_safe_like_pattern(term, "exact") == "test\\_user"

    # ==============================================================================
    # Validation Tests
    # ==============================================================================

    def test_validate_uuid(self):
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        assert db_security.validate_uuid(valid_uuid) is True
        assert db_security.validate_uuid("invalid-uuid") is False
        
        # Sanitize
        assert db_security.sanitize_uuid(valid_uuid.upper()) == valid_uuid.lower()
        assert db_security.sanitize_uuid("invalid") is None

    def test_validate_positive_int(self):
        assert db_security.validate_positive_int("123") == 123
        assert db_security.validate_positive_int("0") is None   # Must be positive
        assert db_security.validate_positive_int("-5") is None
        assert db_security.validate_positive_int("abc") is None
        
    def test_validate_pagination(self):
        # Default
        assert db_security.validate_pagination(None, None) == (1, 20)
        
        # Valid
        assert db_security.validate_pagination("2", "50") == (2, 50)
        
        # Out of bounds / Invalid
        assert db_security.validate_pagination("0", "150", max_limit=100) == (1, 20) # 0 page -> 1, 150 limit but invalid -> default 20? 
        # Actually logic says: if lim > max_limit, condition 0 < lim <= max_limit fails, so it keeps default 20.
        
        assert db_security.validate_pagination("-1", "abc") == (1, 20)
