#!/usr/bin/env python3
"""Analyze real AI test records into mention/recommendation/citation metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.ai_test import analyze_ai_tests  # noqa: E402
from engine.summary.intelligence import normalize_observation  # noqa: E402


def load_tests(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("ai_observations") or raw.get("tests") or raw.get("records") or []
    if not isinstance(raw, list):
        raise ValueError("--tests JSON must be an array or an object with an ai_observations/tests list")
    return [item for item in raw if isinstance(item, dict)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Optional diagnostic report used for company context.")
    parser.add_argument("--tests", required=True, type=Path, help="Path to ai-test.json with real AI answers.")
    parser.add_argument("--output", type=Path, help="Path to write ai-test-result.json.")
    args = parser.parse_args(argv)

    tests = load_tests(args.tests)
    observations = [normalize_observation(item) for item in tests]
    result = analyze_ai_tests(observations)
    context: dict[str, Any] = {}
    if args.input and args.input.exists():
        try:
            report = json.loads(args.input.read_text(encoding="utf-8"))
            meta = report.get("meta") or {}
            company = report.get("company") or {}
            context = {
                "company_name": company.get("name"),
                "engine": meta.get("engine"),
                "report_version": meta.get("version"),
            }
        except (OSError, ValueError):
            context = {}
    result["context"] = context
    result["input_records"] = len(tests)

    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
