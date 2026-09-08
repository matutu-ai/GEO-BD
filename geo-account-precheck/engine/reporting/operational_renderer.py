"""Render a ReportModel as the L2 Operational report for GEO teams."""

from __future__ import annotations

from typing import Any

from .formatting import join, metric_value, number_text, score_text, status_text, text
from .models import ReportModel


def render_operational(model: ReportModel) -> str:
    data = model.to_dict()
    lines: list[str] = [
        "# GEO Operational Report",
        "",
        f"## {text(data['meta'].get('company_name'), '该企业')}",
        "",
        f"- 引擎：{text(data['meta'].get('engine'))} {text(data['meta'].get('version'), '')}".rstrip()
        + f"  ·  Operational Report",
        f"- 生成时间：{text(data['meta'].get('generated_at'), '未记录')}",
        "",
    ]
    _overview_section(lines, data)
    _ai_section(lines, data)
    _query_section(lines, data)
    _competitor_section(lines, data)
    _entity_section(lines, data)
    _evidence_section(lines, data)
    _coverage_section(lines, data)
    _opportunity_section(lines, data)
    _action_section(lines, data)
    _measurement_section(lines, data)
    _data_section(lines, data)
    return "\n".join(lines).rstrip() + "\n"


def _overview_section(lines: list[str], data: dict[str, Any]) -> None:
    health = data["health"]
    lines.extend(["---", "", "## 01 总体诊断", ""])
    if health.get("score") is None:
        lines.extend([f"- GEO Score：{text(health.get('status'))}", f"- 说明：{text(health.get('summary'))}"])
    else:
        lines.extend(
            [
                f"- GEO Score：{score_text(health.get('score'))} / 100",
                f"- 状态：{text(health.get('band'))} · {text(health.get('band_label'))}",
                f"- 数据完整度：{score_text(health.get('data_completeness'))}",
                f"- 说明：{text(health.get('summary'))}",
            ]
        )
    top = data["top_problems"]
    lines.extend(["", "Top 问题：", *[f"- {text(item.get('priority'))}｜{text(item.get('title'))}" for item in top]])
    if not top:
        lines.append("- 数据不足，无法排序 Top 问题。")
    lines.append("")


def _ai_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 02 AI表现", "", "| 核心指标 | 数值 | 状态 | 依据 |", "|---|---|---|---|"])
    for key, metric in data["core_metrics"].items():
        if key.startswith("_") or key == "coverage":
            continue
        lines.append(
            f"| {key} | {metric_value(metric)} | {status_text(metric.get('status'))} | "
            f"{text(metric.get('basis'), '—')} |"
        )
    lines.append("")
    cognition = data["ai_cognition"]
    lines.extend(["AI Observation：", ""])
    observations = cognition.get("observations") or []
    if not observations:
        lines.extend(["- 无真实 Observation；所有 AI 指标保持 UNKNOWN。", ""])
        return
    lines.extend(
        [
            "| Query | 类型 | 提及 | 推荐 | 准确描述 | 引用 | 位置 | 来源 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in observations:
        lines.append(
            f"| {text(item.get('query'))} | {text(item.get('query_type'))} | "
            f"{_yes_no(item.get('company_mentioned'))} | {_yes_no(item.get('company_recommended'))} | "
            f"{_yes_no(item.get('company_correctly_described'))} | {_yes_no(item.get('company_cited'))} | "
            f"{score_text(item.get('position'))} | {join(item.get('sources')) or '—'} |"
        )
    lines.append("")


def _query_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 03 Query Matrix", "", "### 意图聚类", "", "| 意图 | 标签 | Query 数 | Mention | Recommendation | Citation | 场景覆盖 | 状态 |", "|---|---|---|---|---|---|---|---|"])
    clusters = data["query_clusters"]
    if not clusters:
        lines.extend(["| UNKNOWN | - | 0 | - | - | - | - | UNKNOWN |", ""])
    else:
        for cluster in clusters:
            rates = cluster.get("rates") or {}
            lines.append(
                f"| {text(cluster.get('intent'))} | {text(cluster.get('label'), cluster.get('intent', '—'))} | "
                f"{cluster.get('query_count', 0)} | {score_text(rates.get('mention_rate'))} | "
                f"{score_text(rates.get('recommendation_rate'))} | {score_text(rates.get('citation_rate'))} | "
                f"{score_text(rates.get('scenario_coverage'))} | {text(cluster.get('status'))} |"
            )
        lines.append("")
    coverage = (data["core_metrics"].get("coverage") or {})
    lines.extend(
        [
            "### 总体 Coverage",
            "",
            "| 指标 | 数值 |",
            "|---|---|",
            f"| Mention Rate | {score_text(coverage.get('mention_rate'))} |",
            f"| Recommendation Rate | {score_text(coverage.get('recommendation_rate'))} |",
            f"| Description Accuracy | {score_text(coverage.get('description_accuracy'))} |",
            f"| Citation Rate | {score_text(coverage.get('citation_rate'))} |",
            f"| Scenario Coverage | {score_text(coverage.get('scenario_coverage'))} |",
            f"| Coverage Score | {score_text(coverage.get('score'))} |",
            f"| 状态 | {text(coverage.get('status'))} |",
            f"| 说明 | {text(coverage.get('basis'), '—')} |",
            "",
        ]
    )


def _competitor_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 04 Competitor", ""])
    summary = data["competitor_summary"]
    share = summary.get("share_of_voice") or {}
    lines.extend(["### AI Share of Voice", ""])
    share_items = share.get("items") or []
    if share_items:
        lines.extend(["| 主体 | Share | 被提及次数 |", "|---|---|---|"])
        for item in share_items:
            lines.append(
                f"| {text(item.get('name'))} | {number_text(item.get('share'))}% | "
                f"{number_text(item.get('mentioned_in'))} |"
            )
        lines.append("")
    else:
        lines.extend([f"UNKNOWN：{text(share.get('basis'), '没有真实 AI Observation，不估算 Share of Voice。')}", ""])
    lines.extend(["### Competitor Gap", "", "| 竞品 | 状态 | Mention Rate | Recommendation | Evidence | Authority | Citation |", "|---|---|---|---|---|---|---|"])
    competitors = summary.get("competitors") or []
    if not competitors:
        lines.append("| UNKNOWN | - | - | - | - | - | - |")
    else:
        for item in competitors:
            lines.append(
                f"| {text(item.get('name'))} | {text(item.get('status'))} | {score_text(item.get('mention_rate'))} | "
                f"{score_text(item.get('recommendation_rate'))} | {score_text(item.get('evidence_count'))} | "
                f"{score_text(item.get('authority_score'))} | {score_text(item.get('citation_rate'))} |"
            )
    lines.extend(["", "| 维度 | 客户 | 竞品 | 差距 | 状态 |", "|---|---|---|---|---|"])
    gaps = summary.get("gap_edges") or []
    if not gaps:
        lines.append("| UNKNOWN | - | - | - | UNKNOWN |")
    else:
        for item in gaps:
            lines.append(
                f"| {text(item.get('dimension'))} | {score_text(item.get('client_score'))} | "
                f"{score_text(item.get('competitor_score'))} | {score_text(item.get('gap'))} | "
                f"{text(item.get('status'))} |"
            )
    lines.append("")


def _entity_section(lines: list[str], data: dict[str, Any]) -> None:
    consistency = data["entity_consistency"]
    lines.extend(["---", "", "## 05 Entity Consistency", ""])
    lines.extend([f"- 总体：{status_text(consistency.get('status'))}", f"- NAP 一致：{_text_bool(consistency.get('nap_consistent'))}", f"- NAP 完整：{_text_bool(consistency.get('nap_complete'))}", f"- 说明：{text(consistency.get('summary'))}", "", "| 字段 | 当前值 | 状态 |", "|---|---|---|"])
    for row in consistency.get("fields") or []:
        lines.append(
            f"| {text(row.get('field'), '—')} | {text(row.get('value'), '—')} | "
            f"{status_text(row.get('status'))} |"
        )
    conflicts = consistency.get("conflicts") or []
    if conflicts:
        lines.extend(["", "冲突/待核验：", *[f"- {item}" for item in conflicts]])
    lines.append("")


def _evidence_section(lines: list[str], data: dict[str, Any]) -> None:
    conflicts = data["evidence_conflicts"]
    lines.extend(["---", "", "## 06 Evidence", "", "### 冲突检测", ""])
    lines.append(f"- 状态：{text(conflicts.get('status'))}")
    lines.append(f"- 说明：{text(conflicts.get('summary'))}")
    for conflict in conflicts.get("conflicts") or []:
        lines.extend(
            [
                "",
                f"- {text(conflict.get('evidence_id'))}：{text(conflict.get('claim'))}",
                f"  - 冲突对象：{join(conflict.get('conflicts_with'))}",
            ]
        )
    lines.extend(["", "### Evidence 明细", "", "| ID | 声明 | 来源 | 来源类型 | 日期 | 核验 | 状态 |", "|---|---|---|---|---|---|---|"])
    refs = data["evidence_refs"]
    if not refs:
        lines.append("| UNKNOWN | 没有 Evidence 记录 | - | - | - | - | UNKNOWN |")
    else:
        for item in refs:
            lines.append(
                f"| {text(item.get('id'), '—')} | {text(item.get('claim'), '—')} | "
                f"{text(item.get('source'), '—')} | {text(item.get('source_type_label'), item.get('source_type', '—'))} | "
                f"{score_text(item.get('date'))} | {_yes_no(item.get('verified'))} | {text(item.get('status'))} |"
            )
    lines.append("")


def _coverage_section(lines: list[str], data: dict[str, Any]) -> None:
    metrics = data["core_metrics"]
    lines.extend(["---", "", "## 07 Citation / Scenario / Coverage", "", "| 指标 | 数值 | 状态 | 依据 |", "|---|---|---|---|"])
    for key in ("ai_citation", "ai_recommendation", "scenario_coverage", "ai_trust"):
        metric = metrics.get(key) or {}
        lines.append(
            f"| {key} | {metric_value(metric)} | {status_text(metric.get('status'))} | "
            f"{text(metric.get('basis'), '—')} |"
        )
    lines.append("")


def _opportunity_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 08 Opportunity", "", "| 机会 | 机会指数 | 优先级 | 当前表现 | Business | AI Demand | 竞品差距 | 可行性 | 理由 |", "|---|---|---|---|---|---|---|---|---|"])
    opportunities = data["opportunities"]
    if not opportunities:
        lines.append("| UNKNOWN | - | - | - | - | - | - | - | 数据不足 |")
    else:
        for item in opportunities:
            lines.append(
                f"| {text(item.get('title'))} | {score_text(item.get('opportunity_index', item.get('score')))} | "
                f"{text(item.get('priority'))} | {score_text(item.get('current_presence'))} | "
                f"{score_text(item.get('business_value'))} | {score_text(item.get('ai_opportunity'))} | "
                f"{score_text(item.get('competition'))} | {score_text(item.get('feasibility'))} | "
                f"{text(item.get('reason'), '—')} |"
            )
    lines.append("")


def _action_section(lines: list[str], data: dict[str, Any]) -> None:
    lines.extend(["---", "", "## 09 Action Plan", ""])
    actions = data["action_plan"]
    if not actions:
        lines.append("暂无动作；先补齐基础资料、Evidence 与真实 AI Observation。")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for action in actions:
        grouped.setdefault(text(action.get("priority"), "P2"), []).append(action)
    for priority in ("P0", "P1", "P2", "P3"):
        items = grouped.get(priority) or []
        if not items:
            continue
        lines.append(f"### {priority}")
        for action in items:
            lines.append(f"**{text(action.get('title'), action.get('id', ''))}**")
            objective = text(action.get("objective"))
            if objective:
                lines.append(f"- 目标：{objective}")
            tasks = action.get("tasks") or []
            if tasks:
                lines.append(f"- 执行：{join(tasks, '；')}")
            impacts = action.get("expected_impact") or []
            if impacts:
                lines.append(f"- 预计影响：{join(impacts)}")
            materials = action.get("required_materials") or []
            if materials:
                lines.append(f"- 所需资料：{join(materials)}")
            verification = text(action.get("verification"))
            if verification:
                lines.append(f"- 验证：{verification}")
            lines.append("")


def _measurement_section(lines: list[str], data: dict[str, Any]) -> None:
    baseline = data["baseline"]
    measurement = data["measurement"]
    lines.extend(["---", "", "## 10 Measurement", "", f"- Baseline：{text(baseline.get('status'))}", f"- 说明：{text(baseline.get('summary'))}", ""])
    changes = measurement.get("metric_changes") or []
    if changes:
        lines.extend(["| 指标 | Before | After | Delta | 状态 |", "|---|---|---|---|---|"])
        for change in changes:
            delta = change.get("delta")
            lines.append(
                f"| {text(change.get('metric'))} | {score_text(change.get('before'))} | "
                f"{score_text(change.get('after'))} | {delta if delta is None else f'{delta:+g}'} | "
                f"{text(change.get('status'))} |"
            )
        lines.append("")
    plan = measurement.get("plan_steps") or []
    if plan:
        lines.extend(["复测步骤：", *[f"{index}. {step}" for index, step in enumerate(plan, start=1)], ""])


def _data_section(lines: list[str], data: dict[str, Any]) -> None:
    confidence = data["confidence"]
    lines.extend(["---", "", "## 11 数据状态", ""])
    lines.extend(
        [
            f"- 诊断可信度：{score_text(confidence.get('score'))}% · {text(confidence.get('label'))}",
            f"- Data Quality：{score_text(confidence.get('data_quality_score'))} / 100",
            f"- 结论依据：{text(confidence.get('basis'), '—')}",
        ]
    )
    missing = confidence.get("missing_data") or []
    if missing:
        lines.extend(["", "缺失数据：", *[f"- {item}" for item in missing]])
    lines.append("")


def _yes_no(value: Any) -> str:
    return "是" if value else "否"


def _text_bool(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    return "一致" if value else "不一致"
