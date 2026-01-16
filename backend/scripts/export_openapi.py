#!/usr/bin/env python3
"""
Export OpenAPI schema to JSON file.

This script exports the current FastAPI OpenAPI schema to a JSON file.
Used for API contract testing and client generation.

Usage:
    python scripts/export_openapi.py
    python scripts/export_openapi.py --output ../docs/openapi.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


def export_openapi_schema(output_path: str = "openapi.json") -> None:
    """Export OpenAPI schema to JSON file."""
    schema = app.openapi()

    # Ensure the output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"✅ OpenAPI schema exported to: {output_file.absolute()}")
    print(f"   Version: {schema.get('info', {}).get('version', 'unknown')}")
    print(f"   Title: {schema.get('info', {}).get('title', 'unknown')}")
    print(f"   Paths: {len(schema.get('paths', {}))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument(
        "--output", "-o",
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    args = parser.parse_args()

    export_openapi_schema(args.output)
