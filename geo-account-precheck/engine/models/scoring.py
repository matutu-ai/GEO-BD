"""Scoring and opportunity models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import clamp


@dataclass
class Opportunity:
    title: str = ""
    score: int = 0
    priority: str = "P2"
    business_value: int = 0
    ai_demand: int = 0
    competitor_gap: int = 0
    evidence_availability: int = 0
    feasibility: int = 0
    reason: str = ""
    status: str = "INFERENCE"
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "score": self.score,
            "priority": self.priority,
            "business_value": self.business_value,
            "ai_demand": self.ai_demand,
            "competitor_gap": self.competitor_gap,
            "evidence_availability": self.evidence_availability,
            "feasibility": self.feasibility,
            "reason": self.reason,
            "status": self.status,
            "basis": self.basis,
        }

    @staticmethod
    def priority_for(score: int) -> str:
        if score >= 75:
            return "P0"
        if score >= 55:
            return "P1"
        if score >= 35:
            return "P2"
        return "P3"


@dataclass
class ScoreSet:
    entity_score: int | None = None
    ai_cognition_score: int | None = None
    query_coverage_score: int | None = None
    evidence_score: int | None = None
    eeaap_score: int | None = None
    eeat_score: int | None = None
    competitor_gap_score: int | None = None
    citation_score: int | None = None
    trust_score: int | None = None
    scenario_coverage_score: int | None = None
    keyword_coverage_score: int | None = None
    nap_score: int | None = None
    geo_score: int | None = None
    confidence: float | None = None
    data_completeness: float | None = None
    status: str = ""
    basis: dict[str, str] = field(default_factory=dict)
    available_dimensions: list[str] = field(default_factory=list)
    insufficient_dimensions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_score": self.entity_score,
            "ai_cognition_score": self.ai_cognition_score,
            "query_coverage_score": self.query_coverage_score,
            "evidence_score": self.evidence_score,
            "eeaap_score": self.eeaap_score,
            "eeat_score": self.eeat_score,
            "competitor_gap_score": self.competitor_gap_score,
            "citation_score": self.citation_score,
            "trust_score": self.trust_score,
            "scenario_coverage_score": self.scenario_coverage_score,
            "keyword_coverage_score": self.keyword_coverage_score,
            "nap_score": self.nap_score,
            "geo_score": self.geo_score,
            "confidence": self.confidence,
            "data_completeness": self.data_completeness,
            "status": self.status,
            "basis": self.basis,
            "available_dimensions": self.available_dimensions,
            "insufficient_dimensions": self.insufficient_dimensions,
        }

    @staticmethod
    def weighted(values: list[tuple[float, int | None]]) -> int | None:
        available = [(weight, value) for weight, value in values if value is not None]
        if not available:
            return None
        weight_total = sum(weight for weight, _ in available)
        if weight_total <= 0:
            return None
        numerator = sum(weight * value for weight, value in available)
        return clamp(numerator / weight_total)
