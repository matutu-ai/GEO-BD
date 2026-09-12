#!/usr/bin/env python3
"""Run the GEO-BD Diagnostic Skill V1 pre-optimization report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pipeline import DiagnosticPipeline  # noqa: E402
from engine.reporting.diagnostic_skill import (  # noqa: E402
    build_diagnostic_skill_report,
    render_diagnostic_skill_report,
)


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Client materials normalized as diagnostic input JSON.")
    parser.add_argument("--output", type=Path, help="Write the nine-section Markdown diagnostic report.")
    parser.add_argument("--json", type=Path, help="Write the GEO-BD Diagnostic Skill V1 JSON report.")
    parser.add_argument("--offline", action="store_true", help="Keep missing research and AI observations UNKNOWN.")
    parser.add_argument("--summary", action="store_true", help="Print a one-screen diagnostic summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    diagnostic = DiagnosticPipeline(
        offline=args.offline,
        research_mode="offline" if args.offline else "manual",
    ).run(_load(args.input))
    report = build_diagnostic_skill_report(diagnostic)
    markdown = render_diagnostic_skill_report(report)
    if args.output:
        _write(args.output, markdown)
    if args.json:
        _write(args.json, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.output or args.json or args.summary:
        score = report["geo_score"]
        print(f"GEO-BD Diagnostic Skill V1.0: {report['company_status'].get('company_name') or 'UNKNOWN'}")
        print(f"GEO Score: {score['total'] if score['total'] is not None else 'UNKNOWN'} {score['status']}")
        print(f"AI Cognition: {report['ai_cognition']['status']}")
        print(f"Query Coverage: {report['query_coverage']['status']}")
        print(f"Evidence: {report['evidence_trust']['score'] if report['evidence_trust']['score'] is not None else 'UNKNOWN'}")
        print(f"Next: {report['next_phase']['handoff']}")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
