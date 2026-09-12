"""Build an operations-focused GEO status summary from a completed diagnosis.

This module deliberately does not run another analysis pass. It only selects,
counts, and formats values already present in a DiagnosticResult.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


UNKNOWN = "【需客户补充真实资料】"
REAL_MODES = {"observed", "provided"}
INTENT_LABELS = {
    "informational": "品牌/信息搜索",
    "brand": "品牌搜索",
    "product": "产品搜索",
    "local": "地域搜索",
    "scenario": "方案/场景搜索",
    "commercial": "采购/商业搜索",
    "decision": "决策搜索",
    "recommendation": "推荐搜索",
}


class FinalSummaryAgent:
    """Summarize a completed diagnostic without generating new evidence."""

    def build(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        company = diagnostic.get("company") or {}
        entity = diagnostic.get("entity") or {}
        observations = _real_observations(diagnostic)
        return {
            "company_name": _company_name(company, entity),
            "company_position": _company_position(company, entity),
            "geo_stage": _geo_stage(diagnostic, observations),
            "entity_score": (diagnostic.get("scores") or {}).get("entity_score"),
            "ai_cognition_summary": _ai_summary(observations),
            "entity_status": {
                "strength": _entity_strength(company, entity),
                "weakness": _entity_weakness(entity),
            },
            "keyword_status": _keyword_status(diagnostic, observations),
            "user_intent_analysis": _intent_summary(diagnostic, observations),
            "competition_analysis": _competition_summary(diagnostic),
            "core_problem": _core_problem(diagnostic, observations),
            "optimization_priority": _priorities(diagnostic),
            "operation_direction": _operation_direction(diagnostic),
            "final_conclusion": _conclusion(diagnostic, observations),
        }


def render_final_summary(summary: dict[str, Any]) -> str:
    """Render the fixed nine-section operations summary."""

    entity = summary.get("entity_status") or {}
    keywords = summary.get("keyword_status") or {}
    priorities = summary.get("optimization_priority") or {}
    lines = [
        "# GEO客户当前情况总结",
        "",
        f"- 企业：{_text(summary.get('company_name'))}",
        f"- 当前阶段：{_text(summary.get('geo_stage'))}",
        "",
        "## 1. 企业当前AI认知判断",
        "",
        "AI目前如何理解该企业：",
        "",
        _text(summary.get("ai_cognition_summary")),
        "",
        f"建议企业定位：{_text(summary.get('company_position'))}",
        "",
        f"当前阶段：{_text(summary.get('geo_stage'))}",
        "",
        "## 2. 当前优势",
        "",
        _single_bullet(entity.get("strength")),
        "",
        "## 3. 当前不足",
        "",
        _single_bullet(entity.get("weakness")),
        "",
        "## 4. 企业实体完整度",
        "",
        "企业",
        "↓",
        "产品",
        "↓",
        "场景",
        "↓",
        "用户需求",
        "↓",
        "解决方案",
        "↓",
        "信任证明",
        "",
        f"评分：{_score(summary.get('entity_score'))}",
        "",
        "## 5. GEO关键词状态",
        "",
        "已有关键词/Query：",
        "",
        _bullets(keywords.get("covered")),
        "",
        "需要建设或复测：",
        "",
        _bullets(keywords.get("missing")),
        "",
        "## 6. 用户搜索意图判断",
        "",
        _text(summary.get("user_intent_analysis")),
        "",
        "竞品情况：",
        "",
        _text(summary.get("competition_analysis")),
        "",
        "## 7. GEO核心问题总结",
        "",
        f"> {_text(summary.get('core_problem'))}",
        "",
        "## 8. GEO运营优化优先级",
        "",
        "### P0 必须优化",
        "",
        _numbered_or_unknown(priorities.get("P0")),
        "",
        "### P1 建设",
        "",
        _numbered_or_unknown(priorities.get("P1")),
        "",
        "### P2 长期提升",
        "",
        _numbered_or_unknown(priorities.get("P2")),
        "",
        "## 9. 最终运营建议",
        "",
        _text(summary.get("operation_direction")),
        "",
        "最终结论：",
        "",
        _text(summary.get("final_conclusion")),
        "",
    ]
    return "\n".join(lines)


def _real_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    observations = (diagnostic.get("ai_cognition") or {}).get("observations") or []
    return [
        item
        for item in observations
        if str(item.get("status") or item.get("observation_mode") or "").lower() in REAL_MODES
    ]


def _company_name(company: dict[str, Any], entity: dict[str, Any]) -> str:
    name = company.get("name")
    if name:
        return str(name)
    return _first_entity_value(entity, "name") or UNKNOWN


def _company_position(company: dict[str, Any], entity: dict[str, Any]) -> str:
    business = str(company.get("business") or _first_entity_value(entity, "business") or "").strip()
    if not business:
        return UNKNOWN
    if "供应与" in business and "供应商" not in business:
        return business.replace("供应与", "供应商与", 1)
    return business


def _first_entity_value(entity: dict[str, Any], field: str) -> str:
    for item in (entity.get("fields") or {}).get(field) or []:
        value = str(item.get("value") or "").strip()
        if value and value.upper() != "UNKNOWN":
            return value
    return ""


def _geo_stage(diagnostic: dict[str, Any], observations: list[dict[str, Any]]) -> str:
    company = diagnostic.get("company") or {}
    entity = diagnostic.get("entity") or {}
    if not _company_name(company, entity) or not (company.get("business") or _first_entity_value(entity, "business")):
        return "Level 0｜企业资料不足，无法形成稳定实体"
    if not observations:
        return "Level 1｜企业实体已开始整理，AI 可见性尚未完成真实测试"
    recommendation_rate = _observed_rate(observations, "company_recommended")
    citation_rate = _observed_rate(observations, "company_cited")
    if recommendation_rate is not None and recommendation_rate >= 60 and citation_rate is not None and citation_rate >= 40:
        return "Level 3｜已有局部 AI 推荐，需要扩大稳定覆盖"
    return "Level 2｜AI 已在部分 Query 识别企业，但推荐与引用理由不足"


def _ai_summary(observations: list[dict[str, Any]]) -> str:
    if not observations:
        return f"{UNKNOWN} 当前结果没有 observed/provided 的真实 AI 观察，不能判断提及、推荐或引用表现。"
    mentioned = _observed_rate(observations, "company_mentioned")
    recommended = _observed_rate(observations, "company_recommended")
    cited = _observed_rate(observations, "company_cited")
    accurate = _observed_rate(observations, "company_correctly_described")
    return (
        f"基于 {len(observations)} 条真实 AI 观察，企业提及率 {mentioned}%、推荐率 {recommended}%、"
        f"引用率 {cited}%，描述准确率 {accurate}%。AI 已在部分企业、地域或产品 Query 中识别企业，"
        "但尚未形成稳定的全链路推荐与引用认知。"
    )


def _entity_strength(company: dict[str, Any], entity: dict[str, Any]) -> str:
    values = []
    for key, label in (("business", "主营业务"), ("products", "产品"), ("industry", "行业"), ("customers", "目标客户"), ("locations", "地域")):
        value = company.get(key) or _entity_values(entity, key)
        if value:
            values.append(label)
    return "已提供并进入企业实体的字段：" + "、".join(values) + "。" if values else UNKNOWN


def _entity_weakness(entity: dict[str, Any]) -> str:
    missing = [str(item) for item in entity.get("missing") or []]
    if not missing:
        return "当前诊断未记录必填实体缺口；仍需核验来源一致性。"
    return "实体缺失字段：" + "、".join(missing) + "。这些字段不能在没有客户资料时补写。"


def _entity_values(entity: dict[str, Any], field: str) -> list[str]:
    return [str(item.get("value")) for item in (entity.get("fields") or {}).get(field) or [] if item.get("value")]


def _keyword_status(diagnostic: dict[str, Any], observations: list[dict[str, Any]]) -> dict[str, str]:
    queries = (diagnostic.get("query_matrix") or {}).get("queries") or []
    observed_queries = {str(item.get("query") or "") for item in observations}
    safe_queries = [item for item in queries if not _restricted_query(item, diagnostic)]
    covered = [str(item.get("query")) for item in safe_queries if str(item.get("query")) in observed_queries and _query_mentioned(item, observations)]
    missing = [str(item.get("query")) for item in safe_queries if str(item.get("query")) not in covered]
    if not safe_queries:
        return {"covered": UNKNOWN, "missing": UNKNOWN}
    if not observations:
        return {"covered": UNKNOWN, "missing": "已生成 Query，但尚未完成真实 AI 复测。"}
    return {
        "covered": "、".join(covered) if covered else "当前真实观察中没有被提及的安全 Query。",
        "missing": "、".join(missing) if missing else "当前已提供 Query 均有提及记录；仍需持续复测引用与推荐。",
    }


def _restricted_query(query: dict[str, Any], diagnostic: dict[str, Any]) -> bool:
    text = str(query.get("query") or "")
    intelligence = diagnostic.get("competition_intelligence") or {}
    boundary = intelligence.get("qualification_boundary") or []
    forbidden = [claim for item in boundary for claim in item.get("forbidden_claims") or []]
    forbidden.extend(str(item) for item in intelligence.get("restricted_scenarios") or [])
    forbidden.extend(str(item) for item in (intelligence.get("positioning") or {}).get("restricted_scenarios") or [])
    constraints = (diagnostic.get("meta") or {}).get("fact_constraints") or {}
    forbidden.extend(str(item) for item in constraints.get("do_not_claim") or [])
    forbidden.extend(str(item) for item in constraints.get("forbidden_positioning") or [])
    claim_safety = intelligence.get("claim_safety") or []
    if isinstance(claim_safety, dict):
        forbidden.extend(str(item) for item in claim_safety.get("forbidden_claims") or [])
    else:
        forbidden.extend(
            str(claim)
            for item in claim_safety
            if isinstance(item, dict)
            for claim in item.get("forbidden_claims") or []
        )
    return any(claim and claim in text for claim in forbidden)


def _query_mentioned(query: dict[str, Any], observations: list[dict[str, Any]]) -> bool:
    target = str(query.get("query") or "")
    return any(str(item.get("query") or "") == target and item.get("company_mentioned") for item in observations)


def _intent_summary(diagnostic: dict[str, Any], observations: list[dict[str, Any]]) -> str:
    queries = (diagnostic.get("query_matrix") or {}).get("queries") or []
    if not queries:
        return UNKNOWN
    all_types = Counter(str(item.get("intent") or "unknown") for item in queries)
    observed_types = Counter(str(item.get("query_type") or "unknown") for item in observations)
    all_text = "、".join(INTENT_LABELS.get(key, key) for key in all_types)
    observed_text = "、".join(INTENT_LABELS.get(key, key) for key in observed_types) or UNKNOWN
    return f"当前已有 Query 覆盖：{all_text}。真实观察已覆盖：{observed_text}。未出现真实观察的意图不能判断为已覆盖。"


def _competition_summary(diagnostic: dict[str, Any]) -> str:
    competitors = (diagnostic.get("competitors") or {}).get("competitors") or []
    if not competitors:
        return f"{UNKNOWN} 当前没有已确认的竞品对比资料，不能判断竞品排名或相对优势。"
    names = "、".join(str(item.get("name")) for item in competitors if item.get("name")) or UNKNOWN
    gap_score = (diagnostic.get("scores") or {}).get("competitor_gap_score")
    return f"已提供竞品：{names}。现有可比分析分数为 {_score(gap_score)}；该分数只表示诊断缺口，不代表市场排名。"


def _core_problem(diagnostic: dict[str, Any], observations: list[dict[str, Any]]) -> str:
    if not observations:
        return f"当前客户最大问题不是产品或服务能力已被证伪，而是 {UNKNOWN}，无法判断 AI 为什么推荐或不推荐。"
    scores = diagnostic.get("scores") or {}
    query_score = scores.get("query_coverage_score")
    citation_score = scores.get("citation_score")
    return (
        "当前客户最大问题不是已提供资料中的产品信息缺失，而是 AI 在现有真实测试中对企业的"
        f" Query 覆盖（{_score(query_score)}）和来源引用（{_score(citation_score)}）不足，尚未形成稳定的专业认知和推荐理由。"
    )


def _priorities(diagnostic: dict[str, Any]) -> dict[str, list[str]]:
    actions = (diagnostic.get("recommendations") or {}).get("actions") or []
    result = {"P0": [], "P1": [], "P2": []}
    for action in actions:
        priority = str(action.get("priority") or "")
        if priority in result and action.get("task"):
            result[priority].append(str(action["task"]))
    return result


def _operation_direction(diagnostic: dict[str, Any]) -> str:
    priorities = _priorities(diagnostic)
    p0 = "、".join(priorities["P0"][:2]) or UNKNOWN
    p1 = "、".join(priorities["P1"][:2]) or UNKNOWN
    p2 = "、".join(priorities["P2"][:2]) or "使用同一批 Query 复测并记录变化"
    return f"未来90天建议：\n\n30天：执行 P0，重点为{p0}。\n\n60天：建设 P1，重点为{p1}。\n\n90天：推进 P2 或{p2}。"


def _conclusion(diagnostic: dict[str, Any], observations: list[dict[str, Any]]) -> str:
    score = _score((diagnostic.get("scores") or {}).get("geo_score"))
    if not observations:
        return f"当前 GEO 总分：{score}。由于没有真实 AI 观察，结论只能停留在资料级诊断；下一步先补充真实测试。"
    return f"当前 GEO 总分：{score}。企业已有可识别的业务与产品基础，下一步应沿现有 P0/P1 动作补齐证据和 Query 覆盖，再用同一批 Query 复测。"


def _observed_rate(observations: list[dict[str, Any]], field: str) -> int:
    return round(100 * sum(bool(item.get(field)) for item in observations) / len(observations))


def _score(value: Any) -> str:
    return UNKNOWN if value is None else f"{value}/100"


def _text(value: Any) -> str:
    return str(value or UNKNOWN)


def _bullets(value: Any) -> str:
    text = _text(value)
    return "\n".join(f"- {item.strip()}" for item in text.split("、") if item.strip())


def _single_bullet(value: Any) -> str:
    return f"- {_text(value)}"


def _numbered_or_unknown(values: Any) -> str:
    items = [str(item) for item in values or [] if str(item).strip()]
    if not items:
        return f"1. {UNKNOWN} 当前没有该优先级的已生成动作。"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))
