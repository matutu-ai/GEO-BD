"""GEO gap model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import clamp


@dataclass
class GeoGap:
    type: str = ""
    severity: str = "low"
    score: int = 0
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    affected_queries: list[str] = field(default_factory=list)
    competitor_advantage: list[str] = field(default_factory=list)
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "score": self.score,
            "reason": self.reason,
            "evidence": self.evidence,
            "affected_queries": self.affected_queries,
            "competitor_advantage": self.competitor_advantage,
            "recommended_action": self.recommended_action,
        }

    @staticmethod
    def severity_for(gap_score: int, critical_flags: list[str] | None = None) -> str:
        flags = set(critical_flags or [])
        if flags & {"nap_conflict", "no_basics"}:
            return "critical"
        if flags & {"unknown_data", "no_queries", "no_observations", "no_evidence", "no_competitors"}:
            return "high"
        if gap_score >= 80:
            return "critical"
        if gap_score >= 55:
            return "high"
        if gap_score >= 30:
            return "medium"
        return "low"

    @staticmethod
    def make(
        gap_type: str,
        health_score: int | None,
        reason: str,
        affected_queries: list[str] | None = None,
        competitor_advantage: list[str] | None = None,
        evidence: list[str] | None = None,
        critical_flags: list[str] | None = None,
        recommended_action: str = "",
    ) -> "GeoGap":
        score = 0 if health_score is None else clamp(100 - health_score)
        severity = GeoGap.severity_for(score, critical_flags)
        if not recommended_action:
            recommended_action = f"补齐 {gap_type.replace('_', ' ')} 相关真实资料并按诊断结论复测"
        return GeoGap(
            type=gap_type,
            severity=severity,
            score=score,
            reason=reason,
            affected_queries=list(affected_queries or []),
            competitor_advantage=list(competitor_advantage or []),
            evidence=list(evidence or []),
            recommended_action=recommended_action,
        )
