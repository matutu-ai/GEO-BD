#!/usr/bin/env python3
"""GEO Diagnostic Engine V3 command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pipeline import DiagnosticPipeline  # noqa: E402
from engine.reporting import (  # noqa: E402
    REPORT_LEVELS,
    build_report_model,
    generate_report,
    render_legacy_report,
)
from engine.validation.schema_validator import validate_against_schema_file  # noqa: E402
from agents.final_summary_agent import render_final_summary  # noqa: E402


def render_input_template() -> str:
    template_path = ROOT / "inputs" / "diagnostic-template.json"
    return template_path.read_text(encoding="utf-8")


def _load_input(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _write_all_reports(
    directory: Path,
    diagnostic: dict[str, Any],
    model: Any,
    *,
    diagnostic_json_path: Path,
    report_json_path: Path,
) -> None:
    """Write executive/operational/technical markdown plus both JSON artifacts."""
    directory.mkdir(parents=True, exist_ok=True)
    _write(directory / "executive.md", generate_report(diagnostic, "executive", model))
    _write(directory / "operational.md", generate_report(diagnostic, "operational", model))
    _write(directory / "technical.md", generate_report(diagnostic, "technical", model))
    _write(directory / "geo_summary.md", render_final_summary(diagnostic.get("final_summary") or {}))
    _write(diagnostic_json_path, _json_text(diagnostic))
    _write(report_json_path, _json_text(model.to_dict()))


def _validate_report(path: Path, schema_path: Path | None = None) -> list[str]:
    report = _load_input(path)
    schema_path = schema_path or ROOT / "schemas" / "diagnostic.schema.json"
    return validate_against_schema_file(report, schema_path)


def _insufficient_problems(diagnostic: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    quality = diagnostic.get("data_quality") or {}
    if quality.get("low_quality"):
        problems.append(f"Data Quality 不足（{quality.get('score')}/100），当前诊断结论可信度有限。")
    coverage = (diagnostic.get("query_matrix") or {}).get("coverage") or {}
    if coverage.get("status") == "UNKNOWN":
        problems.append("没有真实 AI 观察结果，Query Coverage 与 AI 认知均按 UNKNOWN 处理。")
    entity = diagnostic.get("entity") or {}
    required = {"name", "business", "products", "customers", "locations"}
    missing = [key for key in required if key in entity.get("missing", [])]
    if missing:
        problems.append(f"企业实体缺少核心字段：{', '.join(missing)}。")
    if not (diagnostic.get("evidence_graph") or {}).get("items"):
        problems.append("没有 Evidence 记录，评分与推荐动作的可信度有限。")
    return problems


def _console_summary(diagnostic: dict[str, Any]) -> str:
    """Render one-screen status so users do not have to open the full report."""

    scores = diagnostic.get("scores") or {}
    geo_score = scores.get("geo_score")
    geo_label = "UNKNOWN" if geo_score is None else str(geo_score)
    status = str(scores.get("status") or "UNKNOWN")
    evidence_score = scores.get("evidence_score")
    evidence_label = "UNKNOWN" if evidence_score is None else f"{evidence_score}/100"

    actions = (diagnostic.get("recommendations") or {}).get("actions") or []
    if actions:
        top = actions[0]
        top_label = f"Top {top.get('priority')}: {top.get('task')}"
    else:
        top_label = "Top: INSUFFICIENT_DATA，先补齐企业资料与真实 AI 观察"

    entity = diagnostic.get("entity") or {}
    missing = [str(item) for item in entity.get("missing") or []]
    missing_label = "、".join(missing[:6])
    if len(missing) > 6:
        missing_label += f" 等 {len(missing)} 项"
    if not missing_label:
        missing_label = "无已知必查缺失"

    ai_tests = diagnostic.get("ai_tests") or {}
    ai_status = str(ai_tests.get("status") or "NOT_RUN")
    ai_total = int(ai_tests.get("total") or 0)

    return "\n".join(
        [
            f"GEO Score: {geo_label} {status}",
            top_label,
            f"Evidence: {evidence_label}",
            f"Missing: {missing_label}",
            f"AI Test: {ai_status}（{ai_total} 条）",
            "Next: 补充真实观察后，用同一批 Query 复测并 compare_reports",
        ]
    )


def _needs_input_markdown(diagnostic: dict[str, Any]) -> str:
    needs: list[str] = []

    def add(item: str) -> None:
        if item not in needs:
            needs.append(item)

    entity = diagnostic.get("entity") or {}
    for field in entity.get("missing") or []:
        add(f"企业字段：{field}")

    observations = (diagnostic.get("ai_cognition") or {}).get("observations") or []
    if not observations:
        add("真实 AI 问答/搜索观察记录（只接受 observed/provided）")

    competitors = (diagnostic.get("competitors") or {}).get("competitors") or []
    if not competitors:
        add("已确认竞品清单及其来源")

    evidence = (diagnostic.get("evidence_graph") or {}).get("items") or []
    for item in evidence:
        item_id = str(item.get("id") or "")
        if not item.get("source"):
            add(f"Evidence {item_id}：来源")
        if not item.get("date"):
            add(f"Evidence {item_id}：日期")

    actions = (diagnostic.get("recommendations") or {}).get("actions") or []
    for priority in ("P0", "P1", "P2", "P3"):
        for action in [item for item in actions if str(item.get("priority")) == priority]:
            for material in action.get("required_materials") or []:
                add(f"{priority} 行动资料：{material}")
            if priority == "P0":
                break
        if priority == "P0":
            break

    lines = ["# 需要补充的资料", ""]
    if needs:
        lines.extend(f"- {item}" for item in needs)
    else:
        lines.append("- 暂无已知缺口；仍建议逐条核验来源后进入复测。")
    return "\n".join(lines).rstrip() + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Path to a natural GEO diagnostic input JSON.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Path for one Markdown report, or a directory when --report-level all is used.",
    )
    parser.add_argument(
        "--json",
        nargs="?",
        const=ROOT / "reports" / "diagnostic.json",
        type=Path,
        metavar="PATH",
        help="Write diagnostic JSON; an optional PATH defaults to reports/diagnostic.json.",
    )
    parser.add_argument(
        "--report-json",
        nargs="?",
        const=ROOT / "reports" / "report.json",
        type=Path,
        metavar="PATH",
        help="Write the V3 ReportModel JSON; an optional PATH defaults to reports/report.json.",
    )
    parser.add_argument(
        "--markdown",
        nargs="?",
        const=ROOT / "reports" / "diagnostic.md",
        type=Path,
        metavar="PATH",
        help="Write Markdown; an optional PATH defaults to reports/diagnostic.md. With --report-level all, PATH is a directory.",
    )
    parser.add_argument(
        "--report-level",
        choices=REPORT_LEVELS,
        default="executive",
        help="V3 report level: executive (default), operational, technical, or all.",
    )
    parser.add_argument(
        "--legacy-report",
        action="store_true",
        help="Keep the old V2 19-chapter diagnostic Markdown instead of the V3 default report.",
    )
    parser.add_argument("--check", action="store_true", help="Exit non-zero when input data is insufficient.")
    parser.add_argument("--template", action="store_true", help="Print the input JSON template.")
    parser.add_argument("--offline", action="store_true", help="Run without network and never invent research results.")
    parser.add_argument(
        "--research-mode",
        choices=("manual", "provided", "external", "offline"),
        default="offline",
        help="Research mode; offline keeps all missing values UNKNOWN.",
    )
    parser.add_argument("--summary", action="store_true", help="Print one-screen summary instead of the full report.")
    parser.add_argument(
        "--needs-input",
        type=Path,
        metavar="PATH",
        help="Write a checklist of missing data to PATH.",
    )
    parser.add_argument(
        "--final-summary",
        type=Path,
        metavar="PATH",
        help="Write the operations-focused GEO customer summary to PATH.",
    )
    parser.add_argument(
        "--validate",
        type=Path,
        metavar="REPORT_JSON",
        help="Validate an existing diagnostic report against diagnostic.schema.json.",
    )
    parser.add_argument("--schema", type=Path, help="Schema path used with --validate.")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    args = _build_parser().parse_args(argv)

    if args.validate:
        errors = _validate_report(args.validate, args.schema)
        if errors:
            print("VALIDATION_ERROR", file=sys.stderr)
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("VALIDATION_OK: report matches diagnostic.schema.json")
        return 0

    if args.template:
        print(render_input_template(), end="")
        return 0

    if not args.input:
        print("run_diagnostic: --input is required unless --template or --validate is used.", file=sys.stderr)
        return 2

    data = _load_input(args.input)
    diagnostic = DiagnosticPipeline(offline=args.offline or args.research_mode == "offline", research_mode=args.research_mode).run(data)
    model = build_report_model(diagnostic)
    level = args.report_level
    write_all = level == "all" and not args.legacy_report
    if args.legacy_report:
        markdown = render_legacy_report(diagnostic)
    elif level == "all":
        markdown = ""
    else:
        markdown = generate_report(diagnostic, level, model)
    output_path = args.output or args.markdown

    if write_all:
        all_dir = output_path or ROOT / "reports"
        json_path = args.json if args.json is not None else all_dir / "diagnostic.json"
        report_json_path = args.report_json if args.report_json is not None else all_dir / "report.json"
        writes_files = not args.summary or output_path is not None or args.json is not None or args.report_json is not None or args.needs_input is not None or args.final_summary is not None
        if writes_files:
            _write_all_reports(
                all_dir,
                diagnostic,
                model,
                diagnostic_json_path=json_path,
                report_json_path=report_json_path,
            )
    else:
        json_path = args.json
        report_json_path = args.report_json
        writes_files = output_path is not None or json_path is not None or report_json_path is not None or args.needs_input is not None or args.final_summary is not None
        if output_path is not None:
            _write(output_path, markdown)
        if json_path is not None:
            _write(json_path, _json_text(diagnostic))
        if report_json_path is not None:
            _write(report_json_path, _json_text(model.to_dict()))

    if args.final_summary is not None:
        _write(args.final_summary, render_final_summary(diagnostic.get("final_summary") or {}))

    if args.needs_input is not None:
        _write(args.needs_input, _needs_input_markdown(diagnostic))

    if writes_files or args.summary:
        print(_console_summary(diagnostic))
    else:
        print(markdown)

    if args.check:
        problems = _insufficient_problems(diagnostic)
        if problems:
            print("DIAGNOSTIC_INSUFFICIENT_DATA", file=sys.stderr)
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
