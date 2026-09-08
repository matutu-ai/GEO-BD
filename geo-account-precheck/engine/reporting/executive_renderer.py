"""Render a ReportModel as the decision-first Executive report."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .formatting import join, metric_value, score_text, status_text, text
from .models import ReportModel


METRIC_ORDER = (
    "ai_cognition",
    "ai_recommendation",
    "ai_citation",
    "ai_trust",
    "scenario_coverage",
)
METRIC_LABELS = {
    "ai_cognition": "AI认知",
    "ai_recommendation": "AI推荐",
    "ai_citation": "AI引用",
    "ai_trust": "AI可信度",
    "scenario_coverage": "场景覆盖",
}


def render_executive(model: ReportModel) -> str:
    data = model.to_dict()
    lines: list[str] = [
        "# GEO诊断报告",
        "",
        f"## {text(data['meta'].get('company_name'), '该企业')}",
        "",
        f"- 引擎：{text(data['meta'].get('engine'))} {text(data['meta'].get('version'), '')}".rstrip()
        + f"  ·  Executive Report",
        f"- 生成时间：{text(data['meta'].get('generated_at'), '未记录')}",
        f"- 研究模式：{text(data['meta'].get('research_mode'))}",
        "",
    ]
    _health_section(lines, data)
    _cognition_section(lines, data)
    _problems_section(lines, data)
    _opportunities_section(lines, data)
    _actions_section(lines, data)
    _measurement_section(lines, data)
    _evidence_section(lines, data)
    return "\n".join(lines).rstrip() + "\n"


def _health_section(lines: list[str], data: dict[str, Any]) -> None:
    health = data["health"]
    score = health.get("score")
    lines.extend(["---", "", "### GEO Health Score", ""])
    if score is None:
        lines.extend(
            [
                "UNKNOWN",
                "",
                f"状态：{text(health.get('status'))}",
                "",
                text(health.get("summary"), "当前数据不足以计算完整 GEO 判断。"),
                "",
            ]
        )
        return
    lines.extend(
        [
            f"{score_text(score)} / 100",
            "",
            text(health.get("band_label"), health.get("band", "UNKNOWN")),
            "",
            text(health.get("summary"), "当前诊断结论基于现有输入与真实观察。"),
            "",
        ]
    )


def _cognition_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## AI现在怎么看你？", ""])
    cognition = data["ai_cognition"]
    if not cognition.get("recognized") and not cognition.get("not_recognized"):
        lines.extend(
            [
                text(cognition.get("summary"), "当前没有真实 AI Observation，无法判断 AI 认知。"),
                "",
                "缺失数据：真实 AI Observation（AI 认知、推荐、引用都需要它）。",
                "",
            ]
        )
    else:
        if cognition.get("recognized"):
            lines.extend(["AI 已经能够做到：", *[f"- {item}" for item in cognition["recognized"]], ""])
        if cognition.get("not_recognized"):
            lines.extend(["仍未稳定做到：", *[f"- {item}" for item in cognition["not_recognized"]], ""])
        if text(cognition.get("gap")):
            lines.extend([f"当前最大的认知缺口：{text(cognition['gap'])}", ""])
    _metric_table(lines, data["core_metrics"])
    if cognition.get("basis"):
        lines.extend(["", f"说明：{text(cognition['basis'])}", ""])


def _metric_table(lines: list[str], core_metrics: dict[str, Any]) -> None:
    lines.extend(
        [
            "| 核心指标 | 数值 | 数据状态 |",
            "|---|---|---|",
        ]
    )
    for key in METRIC_ORDER:
        metric = core_metrics.get(key) or {}
        lines.append(
            f"| {METRIC_LABELS.get(key, key)} | {metric_value(metric)} | "
            f"{status_text(metric.get('status'))} |"
        )
    lines.append("")


def _problems_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 当前最影响GEO的3个问题", ""])
    problems = data["top_problems"]
    if not problems:
        lines.extend(
            [
                "当前数据不足以排序核心问题。",
                "",
                "建议先补齐：企业基础实体资料、Evidence 与真实 AI Observation。",
                "",
            ]
        )
        return
    for problem in problems[:3]:
        lines.extend(
            [
                f"### {text(problem.get('priority'))}｜{text(problem.get('title'))}",
                "",
                f"- 影响：{_stars(problem.get('impact'))}",
                f"- 可信度：{_confidence(problem.get('confidence'))}",
            ]
        )
        why = text(problem.get("why_it_matters"))
        if why:
            lines.extend(["", f"为什么重要：{why}"])
        metrics = problem.get("affected_metrics") or []
        if metrics:
            lines.extend(["", f"影响指标：{join(metrics)}"])
        evidence = problem.get("evidence_ids") or []
        if evidence:
            lines.extend(["", f"相关证据：{join(evidence)}"])
        lines.append("")


def _opportunities_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 最值得抢的3个机会", ""])
    opportunities = data["opportunities"]
    if not opportunities:
        lines.extend(
            [
                "缺少可排序的 Opportunity 数据；当前只做基础诊断，不估算机会分数。",
                "",
            ]
        )
        return
    for index, opportunity in enumerate(opportunities[:3], start=1):
        title = text(opportunity.get("title"), f"机会 {index}")
        lines.extend(
            [
                f"### {index:02d}｜{title}",
                "",
                f"- 机会指数：{score_text(opportunity.get('opportunity_index', opportunity.get('score')))}",
                f"- 优先级：{text(opportunity.get('priority'))}",
                f"- 当前表现：{score_text(opportunity.get('current_presence'))}",
            ]
        )
        reason = text(opportunity.get("reason"))
        if reason:
            lines.extend(["", f"为什么：{reason}"])
        lines.append("")


def _actions_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 接下来怎么做", ""])
    actions = data["action_plan"]
    if not actions:
        lines.extend(["暂无 P0/P1/P2 动作；先补齐基础资料、Evidence 与真实 AI Observation。", ""])
        return
    grouped: dict[str, list[dict[str, Any]]] = {}
    for action in actions:
        grouped.setdefault(text(action.get("priority"), "P2"), []).append(action)
    shown = 0
    for priority in ("P0", "P1", "P2", "P3"):
        if shown >= 8:
            break
        items = grouped.get(priority) or []
        if not items:
            continue
        lines.extend([f"### {priority}", ""])
        for action in items[:3]:
            if shown >= 8:
                break
            shown += 1
            lines.extend([f"**{text(action.get('title'), action.get('id', ''))}**"])
            objective = text(action.get("objective"))
            if objective:
                lines.extend(["", f"目标：{objective}"])
            tasks = action.get("tasks") or []
            if tasks:
                lines.extend(["", "执行：", *[f"{index}. {text(task)}" for index, task in enumerate(tasks, start=1)]])
            impacts = action.get("expected_impact") or []
            if impacts:
                lines.extend(["", f"预计影响：{join(impacts)}"])
            lines.append("")
    if len(actions) > shown:
        lines.extend([f"> 完整动作共 {len(actions)} 条；L2 Operational Report 中继续展开。", ""])


def _measurement_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 复测指标", ""])
    baseline = data["baseline"]
    measurement = data["measurement"]
    if baseline.get("status") == "COMPARISON_READY":
        lines.append("已具备 Before/After 基线，可用同一批 Query 继续比较：")
        changes = measurement.get("metric_changes") or []
        if changes:
            lines.extend(
                [
                    "",
                    "| 指标 | Before | After | 变化 |",
                    "|---|---|---|---|",
                ]
            )
            for change in changes:
                lines.append(
                    f"| {text(change.get('metric'))} | {score_text(change.get('before'))} | "
                    f"{score_text(change.get('after'))} | {change.get('delta'):+g} |"
                )
            lines.append("")
    elif baseline.get("status") == "BASELINE_ONLY":
        lines.extend(
            [
                "已记录 Before 指标；完成第一轮真实 AI 复测后写入 After 再做对比。",
                "",
                f"Before：{join([f'{k}={score_text(v)}' for k, v in (baseline.get('before_metrics') or {}).items()]) or '无'}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "尚未建立基线。",
                "",
                "建议：完成第一轮真实 AI Observation 后建立 Baseline，再以同一批 Query 复测。",
                "",
            ]
        )
    plan_steps = measurement.get("plan_steps") or []
    if plan_steps:
        lines.extend(["复测步骤：", *[f"{index}. {step}" for index, step in enumerate(plan_steps[:5], start=1)], ""])


def _evidence_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 为什么得出这个结论", ""])
    confidence = data["confidence"]
    lines.extend(
        [
            f"- 诊断可信度：{score_text(confidence.get('score'))}% · {text(confidence.get('label'))}",
            f"- 数据质量：{score_text(confidence.get('data_quality_score'))} / 100",
        ]
    )
    refs = data["evidence_refs"]
    lines.append(f"- Evidence 记录：{_evidence_summary(refs)}")
    observation_count = data["ai_cognition"].get("observation_count") or 0
    lines.append(f"- 真实 AI Observation：{observation_count} 条")
    conflicts = data["evidence_conflicts"]
    if conflicts.get("status") == "CONFLICT":
        conflict_summary = text(conflicts.get("summary"))
        lines.append(f"- 冲突：{conflict_summary}")
    else:
        lines.append(f"- 冲突检测：{text(conflicts.get('status'))}")
    missing = confidence.get("missing_data") or []
    if missing:
        lines.extend(["", "数据缺口：", *[f"- {item}" for item in missing]])
    disclaimer = text(confidence.get("disclaimer"))
    if disclaimer:
        lines.extend(["", f"> {disclaimer}"])
    lines.append("")


def _evidence_summary(refs: list[dict[str, Any]]) -> str:
    if not refs:
        return "0 条（当前无 Evidence，状态 UNKNOWN）"
    ids = [str(item.get("id") or "") for item in refs if str(item.get("id") or "")]
    counts = Counter(str(item.get("source_type") or "unknown") for item in refs)
    official = sum(counts.get(key, 0) for key in ("official", "government", "media", "third_party"))
    user = counts.get("user_provided", 0)
    detail = []
    if official:
        detail.append(f"官方/第三方 {official}")
    if user:
        detail.append(f"用户提供 {user}")
    return f"{len(refs)} 条（{join(detail) or '待分类'}）；{join(ids[:8]) or '无 ID'}"


def _stars(value: Any) -> str:
    if value is None:
        return "—"
    try:
        count = int(value)
    except (TypeError, ValueError):
        return "—"
    count = max(0, min(5, count))
    return "★" * count + "☆" * (5 - count)


def _confidence(value: Any) -> str:
    try:
        return f"{round(float(value) * 100)}%"
    except (TypeError, ValueError):
        return "UNKNOWN"
