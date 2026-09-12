"""GEO-BD Diagnostic Skill V1 adapter.

The adapter presents the existing DiagnosticResult as a stable
pre-optimization contract. It does not recalculate V3 indicators.
"""

from __future__ import annotations

from statistics import mean
from typing import Any


QUERY_TYPES = ("brand", "business", "scenario", "commercial")
QUERY_TYPE_ALIASES = {
    "informational": "brand",
    "product": "business",
    "decision": "commercial",
    "recommendation": "commercial",
    "local": "commercial",
    "commercial": "commercial",
}


def build_diagnostic_skill_report(diagnostic: dict[str, Any]) -> dict[str, Any]:
    """Build the stable V1 report shape from a DiagnosticResult."""

    company = diagnostic.get("company") or {}
    entity = diagnostic.get("entity") or {}
    scores = diagnostic.get("scores") or {}
    basis = scores.get("basis") or {}
    coverage = (diagnostic.get("query_matrix") or {}).get("coverage") or {}
    observations = _real_observations(diagnostic)
    eeaap = diagnostic.get("eeaap") or {}
    eeat = diagnostic.get("eeat") or {}
    evidence = diagnostic.get("evidence_graph") or {}
    competitors = diagnostic.get("competitors") or {}
    gaps = diagnostic.get("gaps") or {}
    recommendations = diagnostic.get("recommendations") or {}

    categories = {
        "entity": _score(scores.get("entity_score"), "Entity 完整度", basis.get("entity_score")),
        "ai_visibility": _score(
            scores.get("ai_cognition_score"), "AI Visibility", basis.get("ai_cognition_score")
        ),
        "query_coverage": _score(
            scores.get("query_coverage_score"), "Query Coverage", basis.get("query_coverage_score")
        ),
        "evidence": _score(scores.get("evidence_score"), "Evidence 可信度", basis.get("evidence_score")),
        "authority": _score(
            eeat.get("authoritativeness") if eeat.get("status") == "COMPUTED" else None,
            "Authority 权威度",
            (eeat.get("basis") or {}).get("authoritativeness", "没有足够 EEAT 数据。"),
        ),
    }
    values = [item["value"] for item in categories.values() if item["value"] is not None]
    total = round(mean(values)) if len(values) == len(categories) else None

    return {
        "schema_version": "1.0",
        "report_type": "GEO-BD Diagnostic",
        "company_status": _company_status(company, entity),
        "ai_cognition": _ai_cognition(coverage, observations),
        "query_coverage": _query_coverage(diagnostic, coverage, observations),
        "evidence_trust": _evidence_trust(evidence, eeaap, scores.get("evidence_score")),
        "competitor_gap": _competitor_gap(competitors),
        "geo_score": {
            "total": total,
            "status": "COMPUTED" if total is not None else "INSUFFICIENT_DATA",
            "scale": 100,
            "basis": "五类诊断指标各占 20 分；缺失类别不按 0 计算，五类齐全后才形成总分。",
            "categories": categories,
            "available_categories": [key for key, item in categories.items() if item["value"] is not None],
            "missing_categories": [key for key, item in categories.items() if item["value"] is None],
        },
        "geo_gaps": list(gaps.get("gaps") or []) + _issue_gaps(company),
        "priority_actions": list(recommendations.get("actions") or []),
        "next_phase": {
            "name": "GEO Strategy",
            "handoff": "诊断完成后进入关键词、信源、内容与发布策略设计。",
            "steps": [
                "先补齐 P0 企业实体与官网基础信息。",
                "再补齐 P1 案例、专家、认证和第三方信源。",
                "针对 P2 Query 缺口设计场景型与采购型内容。",
                "行业资产建设作为 P3，完成后用同一批 Query 复测。",
            ],
            "validation": (diagnostic.get("validation") or {}).get("plan") or {},
        },
    }


def render_diagnostic_skill_report(report: dict[str, Any]) -> str:
    """Render the nine-section pre-optimization report."""

    company = report["company_status"]
    ai = report["ai_cognition"]
    query = report["query_coverage"]
    evidence = report["evidence_trust"]
    competitors = report["competitor_gap"]
    score = report["geo_score"]
    lines = [
        "# GEO诊断报告",
        "",
        "> GEO-BD Diagnostic Skill V1.0｜企业 GEO 优化前诊断与背调",
        "",
        "## 01 企业当前状态",
        "",
        f"- 企业：{_text(company.get('company_name'))}",
        f"- 行业：{_list_text(company.get('industry'))}",
        f"- 地域：{_list_text(company.get('location'))}",
        f"- 业务模式：{_text(company.get('business_model'))}",
        f"- 建议定位：{_text(company.get('position'))}",
        f"- 产品：{_list_text(company.get('products'))}",
        f"- 服务：{_list_text(company.get('services'))}",
        f"- 目标客户：{_list_text(company.get('target_customer'))}",
        f"- 实体状态：{company.get('status', 'UNKNOWN')}",
        "",
        "## 02 AI认知分析",
        "",
        f"- 状态：{ai.get('status', 'UNKNOWN')}",
        f"- 品牌认知：{_score_text(ai.get('brand_recognition'))}",
        f"- 业务理解：{_score_text(ai.get('business_understanding'))}",
        f"- 推荐概率：{_score_text(ai.get('recommend_probability'))}",
        f"- 描述准确度：{_score_text(ai.get('accuracy_score'))}",
        f"- 真实观察：{ai.get('observation_count', 0)} 条",
        "",
        "## 03 Query覆盖分析",
        "",
        f"- 状态：{query.get('status', 'UNKNOWN')}",
        f"- Query 总数：{query.get('total', 0)}",
        f"- Query 覆盖分：{_score_text(query.get('score'))}",
        "",
        "| 类型 | 目标数 | 真实观察数 | 状态 |",
        "|---|---:|---:|---|",
    ]
    for item in query.get("by_type", []):
        lines.append(
            f"| {item['type']} | {item['target_count']} | {item['observed_count']} | {item['status']} |"
        )
    lines.extend(
        [
            "",
            "## 04 Evidence可信度",
            "",
            f"- 状态：{evidence.get('status', 'UNKNOWN')}",
            f"- Evidence 数量：{evidence.get('count', 0)}",
            f"- Evidence 分：{_score_text(evidence.get('score'))}",
            f"- 已核验：{evidence.get('verified_count', 0)}",
            f"- 第三方来源：{evidence.get('third_party_count', 0)}",
            f"- 缺口：{_list_text(evidence.get('gaps'))}",
            "",
            "## 05 竞品差距",
            "",
            f"- 状态：{competitors.get('status', 'UNKNOWN')}",
            f"- 竞品数量：{competitors.get('count', 0)}",
            f"- 竞品差距分：{_score_text(competitors.get('score'))}",
            f"- 主要差距：{_list_text(competitors.get('top_gaps'))}",
            "",
            "## 06 GEO Score",
            "",
            f"- 总分：{_score_text(score.get('total'))} / 100",
            f"- 状态：{score.get('status', 'UNKNOWN')}",
            "",
            "| 指标 | 分数 | 状态 |",
            "|---|---:|---|",
        ]
    )
    for item in score.get("categories", {}).values():
        lines.append(f"| {item['label']} | {_score_text(item['value'])} | {item['status']} |")
    lines.extend(["", "## 07 GEO缺口", ""])
    gaps = report.get("geo_gaps") or []
    lines.extend(f"- {item.get('type', 'Gap')}：{item.get('reason', '')}" for item in gaps)
    if not gaps:
        lines.append("- 当前没有可排序的 GEO 缺口。")
    lines.extend(["", "## 08 P0-P3优化建议", ""])
    actions = report.get("priority_actions") or []
    for action in actions:
        lines.append(f"- {action.get('priority', 'P3')}｜{action.get('task', action.get('title', '待补充'))}")
    if not actions:
        lines.append("- 当前数据不足，先补齐企业资料、Evidence 与真实 AI 观察。")
    lines.extend(["", "## 09 下一阶段执行路线", ""])
    lines.append(f"- {report['next_phase']['handoff']}")
    lines.extend(f"- {step}" for step in report["next_phase"]["steps"])
    lines.extend(
        [
            "",
            "> 诊断结果只表示当前资料和真实观察下的状态，不代表任何 AI 平台的排名保证。",
            "",
        ]
    )
    return "\n".join(lines)


def _company_status(company: dict[str, Any], entity: dict[str, Any]) -> dict[str, Any]:
    def values(key: str) -> list[str]:
        raw = company.get(key)
        if isinstance(raw, list):
            return [str(item) for item in raw if str(item).strip()]
        return [str(raw)] if raw else []

    return {
        "company_name": company.get("name") or _entity_value(entity, "name"),
        "industry": values("industry") or _entity_values(entity, "industry"),
        "location": values("locations") or _entity_values(entity, "locations"),
        "business_model": company.get("business") or _entity_value(entity, "business"),
        "position": _position(company, entity),
        "products": _entity_values(entity, "products"),
        "services": _entity_values(entity, "services"),
        "target_customer": values("customers") or _entity_values(entity, "customers"),
        "status": "COMPUTED" if company.get("name") or _entity_value(entity, "name") else "UNKNOWN",
        "missing": list(entity.get("missing") or []),
    }


def _ai_cognition(coverage: dict[str, Any], observations: list[dict[str, Any]]) -> dict[str, Any]:
    status = "OBSERVED" if coverage.get("status") == "OBSERVED" else "UNKNOWN"
    return {
        "brand_recognition": coverage.get("mention_rate") if status == "OBSERVED" else None,
        "business_understanding": coverage.get("description_accuracy") if status == "OBSERVED" else None,
        "recommend_probability": coverage.get("recommendation_rate") if status == "OBSERVED" else None,
        "accuracy_score": coverage.get("description_accuracy") if status == "OBSERVED" else None,
        "status": status,
        "observation_count": len(observations),
        "platforms": sorted({str(item.get("platform")) for item in observations if item.get("platform")}),
        "basis": coverage.get("basis") or "没有真实 AI 观察结果。",
    }


def _query_coverage(
    diagnostic: dict[str, Any], coverage: dict[str, Any], observations: list[dict[str, Any]]
) -> dict[str, Any]:
    queries = (diagnostic.get("query_matrix") or {}).get("queries") or []
    observed_types = {_query_type(item.get("query_type")) for item in observations}
    by_type = []
    for query_type in QUERY_TYPES:
        target_count = sum(
            1 for item in queries if _query_type(item.get("intent") or item.get("query_type")) == query_type
        )
        observed_count = sum(1 for item in observations if _query_type(item.get("query_type")) == query_type)
        by_type.append(
            {
                "type": query_type,
                "target_count": target_count,
                "observed_count": observed_count,
                "status": "OBSERVED" if query_type in observed_types else "NOT_RUN" if queries else "UNKNOWN",
            }
        )
    return {
        "status": coverage.get("status", "UNKNOWN"),
        "score": coverage.get("score"),
        "total": len(queries),
        "observed": len(observations),
        "by_type": by_type,
        "basis": coverage.get("basis") or "没有目标 Query。",
    }


def _evidence_trust(evidence: dict[str, Any], eeaap: dict[str, Any], score: Any) -> dict[str, Any]:
    items = list(evidence.get("items") or [])
    return {
        "status": "COMPUTED" if items else "UNKNOWN",
        "score": score if isinstance(score, (int, float)) and not isinstance(score, bool) else None,
        "count": len(items),
        "verified_count": sum(1 for item in items if item.get("verified")),
        "third_party_count": sum(
            1 for item in items if item.get("source_type") in {"third_party", "media", "government"}
        ),
        "gaps": list(eeaap.get("gaps") or []),
        "basis": eeaap.get("basis") or "没有 Evidence 记录。",
    }


def _competitor_gap(competitors: dict[str, Any]) -> dict[str, Any]:
    matrix = [item for item in competitors.get("gap_matrix") or [] if item.get("gap") is not None]
    return {
        "status": competitors.get("status", "UNKNOWN"),
        "score": competitors.get("score"),
        "count": len(competitors.get("competitors") or []),
        "top_gaps": [
            item.get("dimension")
            for item in sorted(matrix, key=lambda item: item.get("gap", 0), reverse=True)[:5]
        ],
        "basis": competitors.get("basis") or "没有可靠竞品数据。",
    }


def _position(company: dict[str, Any], entity: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(company.get("business") or ""),
            *[str(item) for item in company.get("products") or []],
            *[str(item) for item in company.get("services") or []],
            *_entity_values(entity, "business"),
            *_entity_values(entity, "products"),
            *_entity_values(entity, "services"),
        ]
    )
    if "通风" in text:
        return "人防通风系统供应商"
    if company.get("business"):
        return "企业业务与配套服务商"
    return "企业业务待确认"


def _issue_gaps(company: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": "Content Gap",
            "severity": "high",
            "score": 0,
            "reason": str(issue),
            "evidence": [],
            "affected_queries": [],
            "competitor_advantage": [],
            "recommended_action": "补充有证据支持的专题内容并用同一批 Query 复测。",
        }
        for issue in company.get("issues") or []
        if str(issue).strip()
    ]


def _real_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    observations = (diagnostic.get("ai_cognition") or {}).get("observations") or []
    return [
        item
        for item in observations
        if str(item.get("status") or item.get("observation_mode")) in {"observed", "provided"}
    ]


def _query_type(value: Any) -> str:
    value = str(value or "").strip().lower()
    return value if value in QUERY_TYPES else QUERY_TYPE_ALIASES.get(value, "scenario")


def _score(value: Any, label: str, basis: Any) -> dict[str, Any]:
    valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    return {
        "value": value if valid else None,
        "label": label,
        "status": "COMPUTED" if valid else "UNKNOWN",
        "basis": str(basis or "没有足够数据。"),
    }


def _entity_values(entity: dict[str, Any], key: str) -> list[str]:
    values = []
    for item in entity.get("fields", {}).get(key, []):
        value = item.get("value") if isinstance(item, dict) else ""
        if value and str(value).upper() != "UNKNOWN":
            values.append(str(value))
    return values


def _entity_value(entity: dict[str, Any], key: str) -> str:
    return (_entity_values(entity, key) or [""])[0]


def _text(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "UNKNOWN"
    return str(value or "UNKNOWN")


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "暂无"
    return str(value or "暂无")


def _score_text(value: Any) -> str:
    return "UNKNOWN" if value is None else str(value)
