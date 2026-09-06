"""Scenario, keyword, citation and NAP summary blocks for diagnostics."""

from __future__ import annotations

from typing import Any

from ..common import UNKNOWN, clamp, is_unknown

NOT_RUN = "NOT_RUN"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

RECOGNITION_TARGETS = {
    "brand": "Brand Recognition 企业认知",
    "product": "Product Recognition 产品认知",
    "scenario": "Scenario Recognition 场景认知",
    "decision": "Decision Recognition 决策认知",
    "recommendation": "Recommendation Recognition 推荐认知",
}


def build_scenario_keyword_blocks(result: dict[str, Any]) -> dict[str, Any]:
    """Derive scenario and keyword intelligence strictly from pipeline signals."""
    matrix = result.get("query_matrix") or {}
    queries = matrix.get("queries") or []
    coverage = matrix.get("coverage") or {}
    cognition = result.get("ai_cognition") or {}
    observations = cognition.get("observations") or []
    real_observations = [
        item
        for item in observations
        if str(item.get("status") or item.get("observation_mode")) in {"observed", "provided"}
    ]

    status = NOT_RUN if queries and not real_observations else UNKNOWN if not queries else "COMPUTED"
    target_types = _recognition_types(result)
    real_intents = {str(item.get("query_type") or _intent(item)) for item in real_observations}
    target_scenarios = _scenarios_from_queries(queries)
    scenarios = [
        {
            "type": query_type,
            "label": RECOGNITION_TARGETS.get(query_type, query_type),
            "target_count": len(target_scenarios.get(query_type, [])),
            "covered_count": len(real_intents & {query_type}),
            "coverage": (
                clamp(100 * len(real_intents & {query_type}) / len(target_scenarios[query_type]))
                if target_scenarios.get(query_type)
                else None
            ),
            "status": "OBSERVED" if real_intents & {query_type} else NOT_RUN if real_observations else NOT_RUN,
        }
        for query_type in ("brand", "product", "scenario", "decision", "recommendation")
        if query_type in target_types
    ]

    target_count = max(len(queries), 1)
    keyword_coverage = (
        clamp(100 * len(real_intents) / target_count)
        if real_observations and real_intents and status == "COMPUTED"
        else None
    )
    keywords = [
        {
            "keyword": str(item.get("query") or "").strip(),
            "type": _keyword_type(item),
            "intent": str(item.get("intent") or _intent(item)),
            "scenario": str(item.get("scenario") or "").strip(),
            "priority": "P0" if str(item.get("query")) in {str(obs.get("query")) for obs in real_observations} else "P3",
        }
        for item in queries
        if str(item.get("query") or "").strip()
    ]
    return {
        "status": status,
        "scenario_status": status,
        "keyword_status": status,
        "target_scenarios": target_scenarios,
        "scenarios": scenarios,
        "scenario_coverage": coverage.get("scenario_coverage") if coverage.get("status") == "OBSERVED" else None,
        "keyword_coverage": keyword_coverage,
        "scenario_coverage_score": _scenario_score(coverage),
        "keyword_coverage_score": keyword_coverage,
        "keywords": keywords,
        "covered_types": sorted({str(item.get("query_type")) for item in real_observations}),
        "basis": _scenario_basis(status, queries),
    }


def _keyword_type(item: dict[str, Any]) -> str:
    intent = str(item.get("intent") or _intent(item))
    type_map = {
        "informational": "Brand Keywords",
        "product": "Product Keywords",
        "recommendation": "Recommendation Keywords",
        "decision": "Decision Keywords",
        "comparison": "Decision Keywords",
        "scenario": "Scenario Keywords",
        "local": "Location Keywords",
        "problem": "Pain Point Keywords",
        "commercial": "Commercial Keywords",
    }
    return type_map.get(intent, "Scenario Keywords")


def _recognition_types(result: dict[str, Any]) -> set[str]:
    company = result.get("company") or {}
    entity = result.get("entity") or {}
    name = company.get("name") or _first_entity_value(entity, "name")
    business = company.get("business") or _first_entity_value(entity, "business")
    types = {"brand", "scenario", "decision", "recommendation"}
    if business and not is_unknown(business):
        types.add("product")
    if not name or is_unknown(name):
        types.clear()
    return types


def _scenarios_from_queries(queries: list[dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for query in queries:
        intent = str(query.get("intent") or _intent(query))
        scenario = str(query.get("scenario") or query.get("query") or "").strip()
        if scenario:
            result.setdefault(intent, []).append(scenario)
    return result


def _scenario_basis(status: str, queries: list[dict[str, Any]]) -> str:
    if not queries:
        return "没有目标场景或 Query，Scenario/Keyword 覆盖无法计算。"
    if status == NOT_RUN:
        return f"已生成 {len(queries)} 条目标 Query；没有真实 AI 测试结果，覆盖率保持 NOT_RUN。"
    return "覆盖率基于同一批 Query 的真实 AI 测试结果计算，不含模拟推测。"


def _scenario_score(coverage: dict[str, Any]) -> int | None:
    if coverage.get("status") == "OBSERVED":
        value = coverage.get("scenario_coverage")
        return int(value) if value is not None else None
    return None


def build_citation_block(result: dict[str, Any]) -> dict[str, Any]:
    """Citation/Mention summary. Real observations only; otherwise NOT_RUN."""
    cognition = result.get("ai_cognition") or {}
    observations = cognition.get("observations") or []
    real = [
        item
        for item in observations
        if str(item.get("status") or item.get("observation_mode")) in {"observed", "provided"}
    ]
    matrix = result.get("query_matrix") or {}
    coverage = matrix.get("coverage") or {}
    competitors_mentioned: list[str] = []
    for item in real:
        for name in item.get("competitors_mentioned") or []:
            if name not in competitors_mentioned:
                competitors_mentioned.append(str(name))

    if not real:
        return {
            "status": NOT_RUN,
            "basis": "没有真实 AI 测试结果；Mention/Recommendation/Citation 指标全部 NOT_RUN，不计算数字。",
            "mention_rate": None,
            "recommendation_rate": None,
            "citation_rate": None,
            "competitor_mention_rate": None,
            "source_coverage": None,
            "competitors_mentioned": competitors_mentioned,
        }
    mentioned = sum(1 for item in real if item.get("company_mentioned"))
    recommended = sum(1 for item in real if item.get("company_recommended"))
    cited = sum(1 for item in real if item.get("company_cited"))
    sources = [source for item in real for source in (item.get("sources") or []) if source]
    return {
        "status": "COMPUTED",
        "basis": "基于用户提供的真实 AI 测试结果计算。",
        "mention_rate": clamp(100 * mentioned / len(real)),
        "recommendation_rate": clamp(100 * recommended / len(real)),
        "citation_rate": clamp(100 * cited / len(real)),
        "competitor_mention_rate": clamp(100 * len([item for item in real if item.get("competitors_mentioned")]) / len(real)),
        "source_coverage": clamp(100 * len(set(sources)) / len(real)) if sources else 0,
        "competitors_mentioned": competitors_mentioned,
        "coverage_observed": coverage.get("status") == "OBSERVED",
    }


def build_nap_block(result: dict[str, Any]) -> dict[str, Any]:
    """NAP/trust consistency: only flags conflicts when comparable fields exist."""
    entity = result.get("entity") or {}
    company = result.get("company") or {}
    name = company.get("name") or _first_entity_value(entity, "name") or ""
    website = _first_entity_value(entity, "website") or ""
    phone = _first_entity_value(entity, "contacts") or ""
    address = _first_entity_value(entity, "address") or ""
    fields = {
        "name": _single(name),
        "website": _single(website),
        "phone": _single(phone),
        "address": _single(address),
    }
    known = {key: value for key, value in fields.items() if value}
    entity_fields = entity.get("fields") or {}
    conflicts: list[str] = []
    if len(set(_entity_values(entity_fields.get("website")))) > 1:
        conflicts.append("官网字段存在多个不一致值")
    phone_values = _entity_values(entity_fields.get("contacts")) + _entity_values(entity_fields.get("phone"))
    if len(set(phone_values)) > 1:
        conflicts.append("联系电话字段存在多个不一致值")
    reported_issue = any(
        isinstance(item, str) and any(token in item for token in ("电话", "官网", "NAP"))
        for item in (company.get("issues") or [])
    )

    if not known:
        return {
            "status": INSUFFICIENT_DATA,
            "basis": "没有可比较的 Name/Address/Phone 信息，NAP 一致性不做猜测。",
            "fields": fields,
            "conflicts": [],
            "complete": False,
            "consistent": None,
        }
    return {
        "status": "COMPUTED",
        "basis": "已发现 NAP 冲突或电话/官网露出问题。" if conflicts or reported_issue else "已知字段内部一致；未检测到 NAP 冲突。",
        "fields": fields,
        "conflicts": conflicts + (["用户上报电话/官网露出问题"] if reported_issue else []),
        "complete": len(known) >= 3,
        "consistent": not conflicts and not reported_issue,
    }


def normalize_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Merge flat ai-test records into the engine's AIObservation shape."""
    item = dict(observation)
    if "query" not in item and "query_text" in item:
        item["query"] = item["query_text"]
    if "company_cited" not in item and "citation_found" in item:
        item["company_cited"] = bool(item.pop("citation_found", False))
    if "query_type" not in item:
        from ..query.intent import classify_query

        item["query_type"] = classify_query(str(item.get("query") or ""), bool(item.get("company_mentioned", False)))
    item.setdefault("observation_mode", "provided")
    item.setdefault("status", "provided")
    item.setdefault("company_correctly_described", False)
    return item


def _first_entity_value(entity: dict[str, Any], key: str) -> str:
    for item in (entity.get("fields") or {}).get(key) or []:
        value = str(item.get("value") or "").strip()
        if value and not is_unknown(value):
            return value
    return ""


def _entity_values(raw: Any) -> list[str]:
    return [str(item.get("value") or "").strip() for item in raw or [] if str(item.get("value") or "").strip()]


def _single(value: str) -> str:
    return value.split("、")[0].split(",")[0].strip() if value else ""


def _intent(query: dict[str, Any]) -> str:
    from ..query.intent import classify_query

    return classify_query(str(query.get("query") or ""), bool(query.get("company_mentioned")))
