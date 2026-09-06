"""Query matrix and coverage models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Query:
    query: str = ""
    intent: str = "unknown"
    root: str = ""
    scenario: str = ""
    industry: str = ""
    location: str = ""
    demand: str = ""
    pain_point: str = ""
    business_value: int = 0
    ai_demand: int = 0
    status: str = "INFERENCE"
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "intent": self.intent,
            "root": self.root,
            "scenario": self.scenario,
            "industry": self.industry,
            "location": self.location,
            "demand": self.demand,
            "pain_point": self.pain_point,
            "business_value": self.business_value,
            "ai_demand": self.ai_demand,
            "status": self.status,
            "source": self.source,
        }


@dataclass
class QueryCoverage:
    total: int = 0
    mentioned: int = 0
    recommended: int = 0
    correctly_described: int = 0
    cited: int = 0
    mention_rate: float | None = None
    recommendation_rate: float | None = None
    description_accuracy: float | None = None
    citation_rate: float | None = None
    scenario_coverage: float | None = None
    score: int | None = None
    status: str = "UNKNOWN"
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "mentioned": self.mentioned,
            "recommended": self.recommended,
            "correctly_described": self.correctly_described,
            "cited": self.cited,
            "mention_rate": self.mention_rate,
            "recommendation_rate": self.recommendation_rate,
            "description_accuracy": self.description_accuracy,
            "citation_rate": self.citation_rate,
            "scenario_coverage": self.scenario_coverage,
            "score": self.score,
            "status": self.status,
            "basis": self.basis,
        }
