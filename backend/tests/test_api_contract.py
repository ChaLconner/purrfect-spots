"""
Tests for API contract checking scripts.
"""

# Import the module we're testing
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_api_breaking_changes import check_non_breaking_changes, compare_schemas


class TestCompareSchemas:
    """Tests for compare_schemas function."""

    def test_no_changes(self):
        """Test with identical schemas - no breaking changes."""
        schema = {"paths": {"/api/v1/users": {"get": {"parameters": [], "responses": {"200": {}}}}}}

        changes = compare_schemas(schema, schema)
        assert len(changes) == 0

    def test_endpoint_removed(self):
        """Test detection of removed endpoint."""
        baseline = {"paths": {"/api/v1/users": {"get": {}}, "/api/v1/cats": {"get": {}}}}
        current = {"paths": {"/api/v1/users": {"get": {}}}}

        changes = compare_schemas(baseline, current)
        assert len(changes) == 1
        assert changes[0]["type"] == "endpoint_removed"
        assert "/api/v1/cats" in changes[0]["path"]

    def test_method_removed(self):
        """Test detection of removed HTTP method."""
        baseline = {"paths": {"/api/v1/users": {"get": {}, "post": {}}}}
        current = {"paths": {"/api/v1/users": {"get": {}}}}

        changes = compare_schemas(baseline, current)
        assert len(changes) == 1
        assert changes[0]["type"] == "method_removed"
        assert "POST" in changes[0]["path"]

    def test_required_param_removed(self):
        """Test detection of removed required parameter."""
        baseline = {
            "paths": {
                "/api/v1/users": {
                    "get": {"parameters": [{"name": "user_id", "required": True}, {"name": "limit", "required": False}]}
                }
            }
        }
        current = {"paths": {"/api/v1/users": {"get": {"parameters": [{"name": "limit", "required": False}]}}}}

        changes = compare_schemas(baseline, current)
        assert len(changes) == 1
        assert changes[0]["type"] == "required_param_removed"
        assert "user_id" in changes[0]["message"]

    def test_optional_param_removed_no_breaking_change(self):
        """Test that removing optional parameter is NOT a breaking change."""
        baseline = {"paths": {"/api/v1/users": {"get": {"parameters": [{"name": "limit", "required": False}]}}}}
        current = {"paths": {"/api/v1/users": {"get": {"parameters": []}}}}

        changes = compare_schemas(baseline, current)
        assert len(changes) == 0

    def test_response_removed(self):
        """Test detection of removed response code."""
        baseline = {"paths": {"/api/v1/users": {"get": {"responses": {"200": {}, "404": {}}}}}}
        current = {"paths": {"/api/v1/users": {"get": {"responses": {"404": {}}}}}}

        changes = compare_schemas(baseline, current)
        assert len(changes) == 1
        assert changes[0]["type"] == "response_removed"


class TestNonBreakingChanges:
    """Tests for check_non_breaking_changes function."""

    def test_new_endpoint_detected(self):
        """Test that new endpoints are reported as warnings."""
        baseline = {"info": {"version": "1.0.0"}, "paths": {"/api/v1/users": {"get": {}}}}
        current = {"info": {"version": "1.0.0"}, "paths": {"/api/v1/users": {"get": {}}, "/api/v1/cats": {"get": {}}}}

        warnings = check_non_breaking_changes(baseline, current)
        assert len(warnings) == 1
        assert warnings[0]["type"] == "endpoint_added"
        assert "/api/v1/cats" in warnings[0]["path"]

    def test_version_change_detected(self):
        """Test that version changes are reported."""
        baseline = {"info": {"version": "1.0.0"}, "paths": {}}
        current = {"info": {"version": "2.0.0"}, "paths": {}}

        warnings = check_non_breaking_changes(baseline, current)
        assert len(warnings) == 1
        assert warnings[0]["type"] == "version_changed"
        assert "1.0.0" in warnings[0]["message"]
        assert "2.0.0" in warnings[0]["message"]
