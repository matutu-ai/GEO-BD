#!/usr/bin/env python3
"""Validate a GEO Diagnostic Engine report against the V2 schemas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.validation.schema_validator import validate_against_schema_file  # noqa: E402


def load_report(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("report JSON must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to diagnostic.json.")
    parser.add_argument(
        "--schema",
        type=Path,
        default=ROOT / "schemas" / "diagnostic.schema.json",
        help="Path to diagnostic.schema.json.",
    )
    parser.add_argument("--check", action="store_true", help="Exit non-zero when validation fails.")
    args = parser.parse_args(argv)

    report = load_report(args.input)
    errors = validate_against_schema_file(report, args.schema)
    if errors:
        print(f"VALIDATION_ERROR: {len(errors)} problem(s)", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("VALIDATION_OK: report matches diagnostic.schema.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
