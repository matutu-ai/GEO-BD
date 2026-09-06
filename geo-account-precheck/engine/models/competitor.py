"""Competitor intelligence models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import clamp


@dataclass
class Competitor:
    name: str = ""
    status: str = "candidate"
    mention_rate: int | None = None
    recommendation_rate: int | None = None
    evidence_count: int | None = None
    authority_score: int | None = None
    citation_rate: int | None = None
    dimensions: dict[str, int | None] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Any) -> "Competitor":
        if isinstance(data, str):
            return cls(name=data, status="candidate")
        if not isinstance(data, dict):
            return cls(name=str(data), status="candidate")
        return cls(
            name=str(data.get("name") or "").strip(),
            status=str(data.get("status") or "candidate"),
            mention_rate=_int_or_none(data.get("mention_rate")),
            recommendation_rate=_int_or_none(data.get("recommendation_rate")),
            evidence_count=_int_or_none(data.get("evidence_count")),
            authority_score=_int_or_none(data.get("authority_score")),
            citation_rate=_int_or_none(data.get("citation_rate")),
            dimensions={str(k): _int_or_none(v) for k, v in (data.get("dimensions") or {}).items()},
            sources=list(data.get("sources") or []),
        )


@dataclass
class CompetitorDimensionGap:
    dimension: str = ""
    client_score: int | None = None
    competitor_score: int | None = None
    gap: int | None = None
    status: str = "UNKNOWN"
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "client_score": self.client_score,
            "competitor_score": self.competitor_score,
            "gap": self.gap,
            "status": self.status,
            "basis": self.basis,
        }


@dataclass
class CompetitorAnalysis:
    competitors: list[Competitor] = field(default_factory=list)
    gap_matrix: list[CompetitorDimensionGap] = field(default_factory=list)
    score: int | None = None
    status: str = "UNKNOWN"
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "competitors": [c.__dict__ for c in self.competitors],
            "gap_matrix": [gap.to_dict() for gap in self.gap_matrix],
            "score": self.score,
            "status": self.status,
            "basis": self.basis,
        }


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value is None else clamp(float(value))
    except (TypeError, ValueError):
        return None
