"""ReportModel: structured JSON model between DiagnosticResult and renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReportModel:
    meta: dict[str, Any] = field(default_factory=dict)
    health: dict[str, Any] = field(default_factory=dict)
    core_metrics: dict[str, Any] = field(default_factory=dict)
    ai_cognition: dict[str, Any] = field(default_factory=dict)
    top_problems: list[dict[str, Any]] = field(default_factory=list)
    opportunities: list[dict[str, Any]] = field(default_factory=list)
    action_plan: list[dict[str, Any]] = field(default_factory=list)
    query_clusters: list[dict[str, Any]] = field(default_factory=list)
    competitor_summary: dict[str, Any] = field(default_factory=dict)
    entity_consistency: dict[str, Any] = field(default_factory=dict)
    evidence_conflicts: dict[str, Any] = field(default_factory=dict)
    baseline: dict[str, Any] = field(default_factory=dict)
    measurement: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    confidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta,
            "health": self.health,
            "core_metrics": self.core_metrics,
            "ai_cognition": self.ai_cognition,
            "top_problems": self.top_problems,
            "opportunities": self.opportunities,
            "action_plan": self.action_plan,
            "query_clusters": self.query_clusters,
            "competitor_summary": self.competitor_summary,
            "entity_consistency": self.entity_consistency,
            "evidence_conflicts": self.evidence_conflicts,
            "baseline": self.baseline,
            "measurement": self.measurement,
            "evidence_refs": self.evidence_refs,
            "confidence": self.confidence,
        }
