#!/usr/bin/env python3
"""
Export OpenAPI Specification

Generates the OpenAPI JSON schema from the FastAPI application and saves it to a file.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_current_schema() -> dict:
    """Get current OpenAPI schema from FastAPI app."""
    from main import app

    return app.openapi()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path where the OpenAPI schema JSON will be saved",
    )
    args = parser.parse_args()

    output_path = Path(args.output)

    print("Getting current schema from FastAPI app...")
    try:
        schema = get_current_schema()
    except Exception as e:
        print(f"Failed to get schema: {e}", file=sys.stderr)
        return 1

    # Ensure target directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        print(f"Exported OpenAPI schema successfully to {output_path}")
    except Exception as e:
        print(f"Failed to write schema to {output_path}: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
