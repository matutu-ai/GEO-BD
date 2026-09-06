#!/usr/bin/env python3
"""Compare a before/after diagnostic pair and render the improvement report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.comparison import compare_reports  # noqa: E402


def load_report(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("report JSON must be an object")
    return data


def render_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# GEO Before / After Comparison",
        "",
        f"- 状态：{comparison.get('status')}",
        f"- Improvement Rate：{comparison.get('improvement_rate')}",
        f"- GEO Score 变化：{comparison.get('geo_score_change')}",
        f"- Scenario Coverage 变化：{comparison.get('scenario_coverage_change')}",
        f"- Mention 变化：{comparison.get('mention_change')}",
        f"- Recommendation 变化：{comparison.get('recommendation_change')}",
        f"- Citation 变化：{comparison.get('citation_change')}",
        f"- 新增 Evidence：{comparison.get('new_evidence', 0)}",
        "",
        "## 模块变化",
        "",
        "| 模块 | Before | After | 变化 | 状态 |",
        "|---|---|---|---|---|",
    ]
    for module in comparison.get("modules") or []:
        lines.append(
            f"| {module.get('metric')} | {_text(module.get('before'))} | {_text(module.get('after'))} | "
            f"{_text(module.get('delta'))} | {module.get('status')} |"
        )
    resolution = comparison.get("problem_resolution") or {}
    lines.extend(
        [
            "",
            "## 问题解决",
            "",
            f"- 已消除 Gap 数：{resolution.get('resolved_count', 0)}",
            f"- 说明：{resolution.get('basis') or '无数据'}",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _text(value: Any) -> str:
    return "UNKNOWN" if value in (None, "", "None") else str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path, help="Path to the baseline diagnostic.json.")
    parser.add_argument("--after", required=True, type=Path, help="Path to the retest diagnostic.json.")
    parser.add_argument("--output", type=Path, help="Path to write comparison.md.")
    args = parser.parse_args(argv)

    before = load_report(args.before)
    after = load_report(args.after)
    comparison = compare_reports(before, after)
    markdown = render_markdown(comparison)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
