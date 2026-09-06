"""Scorecard aggregation for the GEO Diagnostic Engine."""

from __future__ import annotations

from typing import Any

from .common import UNKNOWN, average_int, clamp
from .models.entity import EntityProfile
from .models.evidence import EvidenceScore
from .models.query import QueryCoverage
from .models.scoring import ScoreSet


ENTITY_WEIGHTS = {
    "name": 0.20,
    "business": 0.15,
    "products": 0.08,
    "services": 0.08,
    "customers": 0.08,
    "locations": 0.08,
    "industry": 0.08,
    "website": 0.05,
    "contacts": 0.05,
    "founders": 0.04,
    "experts": 0.03,
    "certificates": 0.03,
    "media": 0.03,
    "negative_information": 0.02,
}

GEO_DIMENSION_WEIGHTS = {
    "entity": 0.10,
    "ai_cognition": 0.15,
    "evidence": 0.20,
    "eeaap": 0.15,
    "eeat": 0.10,
    "scenario": 0.10,
    "keyword": 0.05,
    "citation": 0.10,
    "nap_trust": 0.05,
}

NAP_FIELD_KEYS = {
    "name": ("name",),
    "phone": ("phone", "contacts"),
    "address": ("address", "location", "locations"),
}


def entity_score(entity: EntityProfile) -> int:
    if not entity.is_known("name") or not entity.is_known("business"):
        return 0
    weighted = sum(weight for key, weight in ENTITY_WEIGHTS.items() if entity.is_known(key))
    return clamp(weighted * 100)


def nap_score(entity: EntityProfile) -> int | None:
    """Score NAP completeness from known fields; missing NAP is never a zero."""
    known = [
        key
        for key, field_keys in NAP_FIELD_KEYS.items()
        if any(entity.is_known(field_key) for field_key in field_keys)
    ]
    if not known:
        return None
    return clamp(100 * len(known) / len(NAP_FIELD_KEYS))


def build_scorecard(
    entity: EntityProfile,
    cognition: dict[str, Any],
    coverage: QueryCoverage,
    evidence: EvidenceScore,
    eeaap: dict[str, Any],
    eeat: dict[str, Any],
    competitor_score: int | None,
    data_quality_score: int,
    scenarios: dict[str, Any] | None = None,
    citations: dict[str, Any] | None = None,
    nap: dict[str, Any] | None = None,
) -> ScoreSet:
    entity_value = entity_score(entity)
    entity_value = None if not entity.is_known("name") or not entity.is_known("business") else entity_value
    cognition_value = cognition.get("score")
    evidence_value = evidence.score if evidence.status == "COMPUTED" else None
    eeaap_value = eeaap.get("overall") if eeaap.get("status") == "COMPUTED" else None
    eeat_value = eeat.get("overall") if eeat.get("status") == "COMPUTED" else None

    scenario_value = scenarios.get("scenario_coverage_score") if scenarios.get("status") == "COMPUTED" else None
    keyword_value = scenarios.get("keyword_coverage_score") if scenarios.get("status") == "COMPUTED" else None

    citation_value = citations.get("citation_rate") if citations and citations.get("status") == "COMPUTED" else None
    nap_value = nap_score(entity) if nap and nap.get("status") != "INSUFFICIENT_DATA" else None
    if nap_value is not None and nap and nap.get("consistent") is False:
        nap_value = clamp(nap_value * 0.5)

    trust_value = eeat.get("trustworthiness")
    if eeat.get("status") != "COMPUTED" or not evidence.item_count:
        trust_value = None
    nap_trust_value = average_int([value for value in (nap_value, trust_value) if value is not None]) if any(
        value is not None for value in (nap_value, trust_value)
    ) else None

    coverage_value = coverage.score if coverage.status != UNKNOWN and coverage.score is not None else None
    dimension_values = {
        "entity": entity_value,
        "ai_cognition": cognition_value,
        "evidence": evidence_value,
        "eeaap": eeaap_value,
        "eeat": eeat_value,
        "scenario": scenario_value,
        "keyword": keyword_value,
        "citation": citation_value,
        "nap_trust": nap_trust_value,
    }
    geo_score = ScoreSet.weighted(
        [(GEO_DIMENSION_WEIGHTS[key], value) for key, value in dimension_values.items()]
    )
    if not entity.is_known("name") and not entity.is_known("business"):
        geo_score = None

    available = [key for key, value in dimension_values.items() if value is not None]
    insufficient = [key for key, value in dimension_values.items() if value is None]
    data_completeness = round(len(available) / len(GEO_DIMENSION_WEIGHTS), 2)
    confidence = clamp(100 * (data_completeness * 0.6 + data_quality_score / 100 * 0.4)) / 100
    status = "INSUFFICIENT_DATA" if geo_score is None or data_completeness < 0.5 else "COMPUTED"

    basis = {
        "entity_score": f"已知基础实体字段加权占比：{entity_score(entity)}/100。",
        "ai_cognition_score": str(cognition.get("basis") or "无观察结果时不评分。"),
        "query_coverage_score": coverage.basis or "无覆盖数据。",
        "evidence_score": "Evidence 核验完成；没有 Evidence 时保持不评分。",
        "eeaap_score": "五维评分平均值，评分均指向对应证据。",
        "eeat_score": "四维信任基础评分，与 EEAAP 分开计算。",
        "competitor_gap_score": "竞品可比维度缺口越小，分数越高；无竞品时不评分。",
        "citation_score": "AI 回答中引用企业来源的比例；无真实 AI Test 时 NOT_RUN。",
        "trust_score": "证据核验、第三方来源与 NAP 一致性的综合指标。",
        "scenario_coverage_score": "同一批 Query 的真实观察覆盖目标场景比例。",
        "keyword_coverage_score": "同一批 Query 的真实观察覆盖意图比例。",
        "nap_score": "Name/Address/Phone 已知度与一致性；缺失或冲突时按不足处理。",
        "geo_score": "按 Entity/AI Cognition/Evidence/EEAAP/EEAT/Scenario/Keyword/Citation/NAP 九维加权；"
        "缺失维度不按 0 计算，data_completeness 不足时整体 INSUFFICIENT_DATA。",
    }
    return ScoreSet(
        entity_score=entity_value,
        ai_cognition_score=cognition_value,
        query_coverage_score=coverage_value,
        evidence_score=evidence_value,
        eeaap_score=eeaap_value,
        eeat_score=eeat_value,
        competitor_gap_score=competitor_score,
        citation_score=citation_value,
        trust_score=trust_value,
        scenario_coverage_score=scenario_value,
        keyword_coverage_score=keyword_value,
        nap_score=nap_value,
        geo_score=geo_score,
        confidence=confidence,
        data_completeness=data_completeness,
        status=status,
        basis=basis,
        available_dimensions=available,
        insufficient_dimensions=insufficient,
    )
