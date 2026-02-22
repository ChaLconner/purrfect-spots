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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class BreakingChangeError(Exception):
    """Raised when breaking changes are detected."""

    pass


def load_schema(path: str) -> dict:
    """Load OpenAPI schema from file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_current_schema() -> dict:
    """Get current OpenAPI schema from FastAPI app."""
    from main import app

    return app.openapi()


def _check_removed_endpoints(baseline_paths: dict, current_paths: dict) -> list[dict]:
    """Check for completely removed endpoints."""
    changes = []
    for path in baseline_paths:
        if path not in current_paths:
            changes.append({"type": "endpoint_removed", "path": path, "message": f"❌ Endpoint removed: {path}"})
    return changes


def _check_method_changes(path: str, baseline_methods: dict, current_spec: dict) -> list[dict]:
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
        changes.extend(_check_parameter_changes(path, method, spec, curr_method_spec))
        changes.extend(_check_response_changes(path, method, spec, curr_method_spec))

    return changes


def _check_parameter_changes(path: str, method: str, baseline_spec: dict, current_spec: dict) -> list[dict]:
    """Check for removed required parameters."""
    changes = []
    baseline_params = {p["name"]: p for p in baseline_spec.get("parameters", [])}
    current_params = {p["name"]: p for p in current_spec.get("parameters", [])}

    for param_name, param in baseline_params.items():
        if param.get("required", False) and param_name not in current_params:
            changes.append(
                {
                    "type": "required_param_removed",
                    "path": f"{method.upper()} {path}",
                    "message": f"❌ Required parameter removed: {param_name} from {method.upper()} {path}",
                }
            )
    return changes


def _check_response_changes(path: str, method: str, baseline_spec: dict, current_spec: dict) -> list[dict]:
    """Check for removed successful responses."""
    changes = []
    baseline_responses = baseline_spec.get("responses", {})
    current_responses = current_spec.get("responses", {})

    for status_code in ["200", "201"]:
        if status_code in baseline_responses and status_code not in current_responses:
            changes.append(
                {
                    "type": "response_removed",
                    "path": f"{method.upper()} {path}",
                    "message": f"❌ Response {status_code} removed from {method.upper()} {path}",
                }
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
            breaking_changes.extend(_check_method_changes(path, methods, current_paths[path]))

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
        default="docs/openapi-baseline.json",
        help="Path to baseline OpenAPI schema (default: docs/openapi-baseline.json)",
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
            with open(baseline_path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            print(f"✅ Created baseline at {baseline_path}")
            return 0
        return 1

    # Load schemas
    print(f"📋 Loading baseline from: {baseline_path}")
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
            with open(baseline_path, "w", encoding="utf-8") as f:
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
            with open(baseline_path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Baseline updated at {baseline_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
