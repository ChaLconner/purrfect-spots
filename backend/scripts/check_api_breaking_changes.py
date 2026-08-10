#!/usr/bin/env python3
"""
API Breaking Changes Detector

Compares current OpenAPI schema against a baseline to detect breaking changes.
Breaking changes include:
- Removed endpoints
- Removed required request parameters
- Changed parameter types
- Removed response fields (in 2xx responses)
- Changed response field types

Usage:
    python scripts/check_api_breaking_changes.py
    python scripts/check_api_breaking_changes.py --baseline docs/openapi-baseline.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

# Force UTF-8 encoding on standard output/error to prevent UnicodeEncodeError on Windows
if sys.platform == "win32":
    try:
        reconfigure_out = getattr(sys.stdout, "reconfigure", None)
        if reconfigure_out:
            reconfigure_out(encoding="utf-8")
        reconfigure_err = getattr(sys.stderr, "reconfigure", None)
        if reconfigure_err:
            reconfigure_err(encoding="utf-8")
    except AttributeError:
        # Older Python runtimes may expose streams without reconfigure().
        pass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class BreakingChangeError(Exception):
    """Raised when breaking changes are detected."""

    pass


def load_schema(path: str) -> dict[str, Any]:
    """Load OpenAPI schema from file."""
    with Path(path).open(encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def get_current_schema() -> dict[str, Any]:
    """Get current OpenAPI schema from FastAPI app."""
    from app.main import app

    return app.openapi()


def _check_removed_endpoints(baseline_paths: dict, current_paths: dict) -> list[dict]:
    """Check for completely removed endpoints."""
    changes = []
    for path in baseline_paths:
        if path not in current_paths:
            changes.append({"type": "endpoint_removed", "path": path, "message": f"❌ Endpoint removed: {path}"})
    return changes


def _check_method_changes(
    path: str,
    baseline_methods: dict,
    current_spec: dict,
    baseline_document: dict[str, Any],
    current_document: dict[str, Any],
) -> list[dict]:
    """Check for changes within a specific endpoint path."""
    changes = []
    current_methods = current_spec  # current_spec is actually all methods for the path

    for method, spec in baseline_methods.items():
        if method.startswith("x-"):  # Skip OpenAPI extensions
            continue

        if method not in current_methods:
            changes.append(
                {
                    "type": "method_removed",
                    "path": f"{method.upper()} {path}",
                    "message": f"❌ Method removed: {method.upper()} {path}",
                }
            )
            continue

        # Method exists, check parameters and responses
        curr_method_spec = current_methods[method]
        changes.extend(
            _check_parameter_changes(path, method, spec, curr_method_spec, baseline_document, current_document)
        )
        changes.extend(
            _check_response_changes(path, method, spec, curr_method_spec, baseline_document, current_document)
        )

    return changes


def _check_parameter_changes(
    path: str,
    method: str,
    baseline_spec: dict,
    current_spec: dict,
    baseline_document: dict[str, Any],
    current_document: dict[str, Any],
) -> list[dict]:
    """Check parameter presence, requiredness, and input schema compatibility."""
    changes = []
    baseline_params = {(p["name"], p.get("in", "query")): p for p in baseline_spec.get("parameters", [])}
    current_params = {(p["name"], p.get("in", "query")): p for p in current_spec.get("parameters", [])}

    for (param_name, location), param in baseline_params.items():
        parameter_path = f"{method.upper()} {path} parameter {param_name} ({location})"
        if param.get("required", False) and (param_name, location) not in current_params:
            changes.append(
                {
                    "type": "required_param_removed",
                    "path": f"{method.upper()} {path}",
                    "message": f"❌ Required parameter removed: {param_name} from {method.upper()} {path}",
                }
            )
            continue

        current_param = current_params.get((param_name, location))
        if current_param is None:
            continue
        if param.get("required", False) and not current_param.get("required", False):
            changes.append(
                {
                    "type": "required_param_relaxed",
                    "path": f"{method.upper()} {path}",
                    "message": f"❌ Required parameter is now optional: {param_name} from {method.upper()} {path}",
                }
            )
        changes.extend(
            _compare_schema(
                param.get("schema", {}),
                current_param.get("schema", {}),
                parameter_path,
                "parameter_schema_changed",
                baseline_document,
                current_document,
            )
        )

    baseline_body = baseline_spec.get("requestBody")
    current_body = current_spec.get("requestBody")
    if baseline_body and not current_body:
        changes.append(
            {
                "type": "request_body_removed",
                "path": f"{method.upper()} {path}",
                "message": f"❌ Request body removed from {method.upper()} {path}",
            }
        )
    elif isinstance(baseline_body, dict) and isinstance(current_body, dict):
        baseline_content = baseline_body.get("content", {})
        current_content = current_body.get("content", {})
        for media_type, media_spec in baseline_content.items():
            if media_type not in current_content:
                changes.append(
                    {
                        "type": "request_content_type_removed",
                        "path": f"{method.upper()} {path}",
                        "message": f"❌ Request content type removed: {media_type} from {method.upper()} {path}",
                    }
                )
                continue
            changes.extend(
                _compare_schema(
                    media_spec.get("schema", {}),
                    current_content[media_type].get("schema", {}),
                    f"{method.upper()} {path} request body ({media_type})",
                    "request_schema_changed",
                    baseline_document,
                    current_document,
                )
            )
    return changes


def _check_response_changes(
    path: str,
    method: str,
    baseline_spec: dict,
    current_spec: dict,
    baseline_document: dict[str, Any],
    current_document: dict[str, Any],
) -> list[dict]:
    """Check response presence and successful response schema compatibility."""
    changes = []
    baseline_responses = baseline_spec.get("responses", {})
    current_responses = current_spec.get("responses", {})

    for status_code, raw_baseline_response in baseline_responses.items():
        status_text = str(status_code)
        if status_text.startswith("x-"):
            continue
        if status_code not in current_responses:
            changes.append(
                {
                    "type": "response_removed",
                    "path": f"{method.upper()} {path}",
                    "message": f"❌ Response {status_code} removed from {method.upper()} {path}",
                }
            )
            continue

        if not status_text.startswith("2"):
            continue

        baseline_response = _resolve_schema(raw_baseline_response, baseline_document)
        current_response = _resolve_schema(current_responses[status_code], current_document)
        baseline_content = baseline_response.get("content", {})
        current_content = current_response.get("content", {})
        for media_type, media_spec in baseline_content.items():
            if media_type not in current_content:
                changes.append(
                    {
                        "type": "response_content_type_removed",
                        "path": f"{method.upper()} {path}",
                        "message": f"❌ Response content type removed: {media_type} from {method.upper()} {path}",
                    }
                )
                continue
            changes.extend(
                _compare_schema(
                    media_spec.get("schema", {}),
                    current_content[media_type].get("schema", {}),
                    f"{method.upper()} {path} response {status_code} ({media_type})",
                    "response_schema_changed",
                    baseline_document,
                    current_document,
                )
            )
    return changes


def _resolve_schema(schema: Any, document: dict[str, Any]) -> dict[str, Any]:
    """Resolve local component references for the compatibility checks."""
    if not isinstance(schema, dict):
        return {}
    resolved = schema
    seen: set[str] = set()
    while isinstance(resolved.get("$ref"), str) and resolved["$ref"].startswith("#/"):
        ref = resolved["$ref"]
        if ref in seen:
            break
        seen.add(ref)
        target: Any = document
        for part in ref[2:].split("/"):
            if not isinstance(target, dict):
                target = {}
                break
            target = target.get(part, {})
        if not isinstance(target, dict):
            break
        resolved = target
    return resolved


def _compare_schema(
    baseline_schema: Any,
    current_schema: Any,
    location: str,
    change_type: str,
    baseline_document: dict[str, Any],
    current_document: dict[str, Any],
) -> list[dict]:
    """Return breaking changes where the current schema accepts less input or output."""
    baseline = _resolve_schema(baseline_schema, baseline_document)
    current = _resolve_schema(current_schema, current_document)
    if not baseline:
        return []
    if not current:
        return [
            {
                "type": change_type,
                "path": location,
                "message": f"❌ Schema removed at {location}",
            }
        ]

    # FastAPI uses ``anyOf`` when an endpoint may return a synchronous result
    # or an accepted/background-job result. If the previous schema remains one
    # of the current alternatives, the response contract was widened rather
    # than broken.
    for composition_key in ("anyOf", "oneOf"):
        alternatives = current.get(composition_key)
        if isinstance(alternatives, list):
            for alternative in alternatives:
                if (
                    isinstance(baseline_schema, dict)
                    and isinstance(alternative, dict)
                    and baseline_schema.get("$ref")
                    and baseline_schema.get("$ref") == alternative.get("$ref")
                ):
                    return []
                if not _compare_schema(
                    baseline,
                    alternative,
                    location,
                    change_type,
                    baseline_document,
                    current_document,
                ):
                    return []

    changes: list[dict] = []

    def add(message: str) -> None:
        changes.append({"type": change_type, "path": location, "message": f"❌ {message} at {location}"})

    baseline_type = baseline.get("type")
    current_type = current.get("type")
    if baseline_type and current_type and baseline_type != current_type:
        add(f"Schema type changed from {baseline_type} to {current_type}")
        return changes
    if baseline.get("format") and current.get("format") and baseline["format"] != current["format"]:
        add(f"Schema format changed from {baseline['format']} to {current['format']}")
    if baseline.get("nullable", False) and not current.get("nullable", False):
        add("Schema is no longer nullable")

    baseline_enum = baseline.get("enum")
    current_enum = current.get("enum")
    if (
        isinstance(baseline_enum, list)
        and isinstance(current_enum, list)
        and not set(baseline_enum).issubset(current_enum)
    ):
        add("Schema enum removed previously accepted values")

    for keyword, comparison in (
        ("minLength", lambda old, new: new > old),
        ("minItems", lambda old, new: new > old),
        ("minimum", lambda old, new: new > old),
        ("exclusiveMinimum", lambda old, new: new > old),
        ("maxLength", lambda old, new: new < old),
        ("maxItems", lambda old, new: new < old),
        ("maximum", lambda old, new: new < old),
        ("exclusiveMaximum", lambda old, new: new < old),
    ):
        old_value = baseline.get(keyword)
        new_value = current.get(keyword)
        if (
            isinstance(old_value, (int, float))
            and isinstance(new_value, (int, float))
            and comparison(old_value, new_value)
        ):
            add(f"Schema constraint {keyword} became stricter")

    if baseline_type == "object" or "properties" in baseline:
        baseline_required = set(baseline.get("required", []))
        current_required = set(current.get("required", []))
        if not baseline_required.issubset(current_required):
            add("Required response/request fields were removed")
        if change_type.startswith(("request_", "parameter_")) and not current_required.issubset(baseline_required):
            add("Required request fields were added")

        baseline_properties = baseline.get("properties", {})
        current_properties = current.get("properties", {})
        for property_name, property_schema in baseline_properties.items():
            if property_name not in current_properties:
                add(f"Schema property removed: {property_name}")
                continue
            changes.extend(
                _compare_schema(
                    property_schema,
                    current_properties[property_name],
                    f"{location}.{property_name}",
                    change_type,
                    baseline_document,
                    current_document,
                )
            )

        if baseline.get("additionalProperties") is not False and current.get("additionalProperties") is False:
            add("Schema no longer accepts additional properties")

    if baseline_type == "array" and "items" in baseline:
        changes.extend(
            _compare_schema(
                baseline["items"],
                current.get("items", {}),
                f"{location}[]",
                change_type,
                baseline_document,
                current_document,
            )
        )

    return changes


def compare_schemas(baseline: dict, current: dict) -> list[dict]:
    """
    Compare two OpenAPI schemas and return list of breaking changes.

    Returns:
        List of breaking change dictionaries with 'type', 'path', and 'message' keys
    """
    breaking_changes = []

    baseline_paths = baseline.get("paths", {})
    current_paths = current.get("paths", {})

    # Check for removed endpoints
    breaking_changes.extend(_check_removed_endpoints(baseline_paths, current_paths))

    # Check for method/param/response changes in existing endpoints
    for path, methods in baseline_paths.items():
        if path in current_paths:
            breaking_changes.extend(_check_method_changes(path, methods, current_paths[path], baseline, current))

    return breaking_changes


def check_non_breaking_changes(baseline: dict, current: dict) -> list[dict]:
    """
    Check for non-breaking but notable changes.

    Returns:
        List of warning dictionaries
    """
    warnings = []

    baseline_paths = baseline.get("paths", {})
    current_paths = current.get("paths", {})

    # Check for new endpoints (informational)
    for path in current_paths:
        if path not in baseline_paths:
            warnings.append({"type": "endpoint_added", "path": path, "message": f"ℹ️ New endpoint added: {path}"})

    # Check version change
    baseline_version = baseline.get("info", {}).get("version", "")
    current_version = current.get("info", {}).get("version", "")

    if baseline_version != current_version:
        warnings.append(
            {
                "type": "version_changed",
                "path": "info.version",
                "message": f"ℹ️ API version changed: {baseline_version} → {current_version}",
            }
        )

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for API breaking changes")
    parser.add_argument(
        "--baseline",
        "-b",
        default="../docs/openapi-baseline.json",
        help="Path to baseline OpenAPI schema (default: ../docs/openapi-baseline.json)",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=True,
        help="Exit with error code if breaking changes detected (default: true)",
    )
    parser.add_argument(
        "--update-baseline", action="store_true", help="Update baseline with current schema after check"
    )
    args = parser.parse_args()

    baseline_path = Path(args.baseline)

    # Check if baseline exists
    if not baseline_path.exists():
        print(f"⚠️ No baseline found at {baseline_path}")
        print("   Run with --update-baseline to create initial baseline")

        if args.update_baseline:
            current = get_current_schema()
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            with baseline_path.open("w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            print(f"✅ Created baseline at {baseline_path}")
            return 0
        return 1

    # Load schemas
    try:
        print(f"Loading baseline from: {baseline_path}")
    except UnicodeEncodeError:
        print(f"Loading baseline from: {baseline_path}")
    baseline = load_schema(str(baseline_path))

    print("📋 Getting current schema from FastAPI app...")
    current = get_current_schema()

    # Compare
    print("\n🔍 Checking for breaking changes...\n")

    breaking_changes = compare_schemas(baseline, current)
    warnings = check_non_breaking_changes(baseline, current)

    # Report warnings
    if warnings:
        print("📝 Non-breaking changes detected:")
        for w in warnings:
            print(f"   {w['message']}")
        print()

    # Report breaking changes
    if breaking_changes:
        print("🚨 BREAKING CHANGES DETECTED:")
        for bc in breaking_changes:
            print(f"   {bc['message']}")
        print()
        print(f"Total: {len(breaking_changes)} breaking change(s)")

        # Update baseline if requested before potentially exiting
        if args.update_baseline:
            with baseline_path.open("w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Baseline updated at {baseline_path}")
            return 0  # If we updated the baseline, it's considered successfully acknowledged

        if args.fail_on_breaking:
            print("\n❌ CI check failed due to breaking changes.")
            print("   If these changes are intentional, update the baseline:")
            print("   python scripts/check_api_breaking_changes.py --update-baseline")
            return 1
    else:
        print("✅ No breaking changes detected!")

        # Update baseline if requested
        if args.update_baseline:
            with baseline_path.open("w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Baseline updated at {baseline_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
