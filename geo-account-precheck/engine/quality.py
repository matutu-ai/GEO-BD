"""Data quality accounting for diagnostic output."""

from __future__ import annotations

from typing import Any

from .common import FACT, UNKNOWN, clamp, is_unknown
from .models.cognition import AIObservation
from .models.entity import EntityProfile
from .models.evidence import EvidenceItem
from .models.query import Query

REQUIRED_ENTITY_FIELDS = {
    "name",
    "business",
    "products",
    "customers",
    "locations",
    "industry",
    "founders",
    "experts",
    "certificates",
    "media",
    "website",
    "contacts",
}


def compute_data_quality(
    entity: EntityProfile,
    evidence_items: list[EvidenceItem],
    observations: list[AIObservation],
    queries: list[Query],
) -> dict[str, Any]:
    fact_count = entity.count_status(FACT)
    inference_count = len(queries)
    unknown_count = sum(
        1 for values in entity.fields.values() for item in values if is_unknown(item.value)
    )
    for item in evidence_items:
        if item.status == UNKNOWN:
            unknown_count += 1
        elif item.status == FACT:
            fact_count += 1
    inference_count += sum(1 for observation in observations if observation.status in {"simulated", "inference"})

    verified_count = sum(1 for item in evidence_items if item.verified)
    unverified_count = len(evidence_items) - verified_count
    sources = {
        item.source
        for item in evidence_items
        if item.source and not is_unknown(item.source)
    }
    sources.update(
        item.source for values in entity.fields.values() for item in values if item.source and not is_unknown(item.source)
    )

    entity_completeness = _entity_completeness(entity)
    source_completeness = (
        (sum(1 for item in evidence_items if item.source) / len(evidence_items)) if evidence_items else 0.0
    )
    verification_completeness = (verified_count / len(evidence_items)) if evidence_items else 0.0
    evidence_completeness = _evidence_completeness(evidence_items)
    score = clamp(
        100
        * (
            0.35 * entity_completeness
            + 0.25 * source_completeness
            + 0.20 * verification_completeness
            + 0.20 * evidence_completeness
        )
    )
    return {
        "score": score,
        "low_quality": score < 50,
        "fact_count": fact_count,
        "inference_count": inference_count,
        "unknown_count": unknown_count,
        "verified_count": verified_count,
        "unverified_count": unverified_count,
        "source_count": len(sources),
        "evidence_completeness": clamp(evidence_completeness * 100),
        "source_completeness": clamp(source_completeness * 100),
        "verification_completeness": clamp(verification_completeness * 100),
        "warning": "当前诊断结论可信度有限，先补齐资料再作为执行依据。" if score < 50 else "",
    }


def _entity_completeness(entity: EntityProfile) -> float:
    if not REQUIRED_ENTITY_FIELDS:
        return 0.0
    return sum(1 for key in REQUIRED_ENTITY_FIELDS if entity.is_known(key)) / len(REQUIRED_ENTITY_FIELDS)


def _evidence_completeness(items: list[EvidenceItem]) -> float:
    if not items:
        return 0.0
    categories = {"experience", "evidence", "authoritativeness", "accuracy", "perspective"}
    found = {item.category for item in items} | {_evidence_category(item.claim) for item in items}
    return len(found & categories) / len(categories)


def _evidence_category(claim: str) -> str:
    text = claim.lower()
    if any(keyword in text for keyword in ("案例", "项目", "经验", "experience")):
        return "experience"
    if any(keyword in text for keyword in ("资质", "证书", "专利", "权威", "authority")):
        return "authoritativeness"
    if any(keyword in text for keyword in ("局限", "不适用", "适用场景", "perspective")):
        return "perspective"
    if any(keyword in text for keyword in ("准确", "无夸大", "accuracy")):
        return "accuracy"
    return "evidence"
