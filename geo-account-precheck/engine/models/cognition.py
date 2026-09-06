"""AI cognition observation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import UNKNOWN, is_unknown, stringify


@dataclass
class AIObservation:
    query: str = ""
    query_type: str = "unknown"
    company_mentioned: bool = False
    company_recommended: bool = False
    company_correctly_described: bool = False
    company_cited: bool = False
    competitors_mentioned: list[str] = field(default_factory=list)
    position: int | None = None
    reason: str = ""
    sources: list[str] = field(default_factory=list)
    confidence: int = 0
    observation_mode: str = "unknown"
    status: str = "observed"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AIObservation":
        if not isinstance(data, dict):
            text = stringify(data)
            return cls(
                query=text,
                reason="该条记录不是结构化 AI 回答，未推断任何提及/推荐结果。",
                observation_mode="unknown",
                status=UNKNOWN,
            )
        explicit_mode = data.get("observation_mode")
        mode = str(explicit_mode or "provided")
        return cls(
            query=stringify(data.get("query")),
            query_type=str(data.get("query_type") or "unknown"),
            company_mentioned=bool(data.get("company_mentioned", False)),
            company_recommended=bool(data.get("company_recommended", False)),
            company_correctly_described=bool(
                data.get("company_correctly_described", data.get("correctly_described", False))
            ),
            company_cited=bool(data.get("company_cited", data.get("cited", False))),
            competitors_mentioned=list(data.get("competitors_mentioned") or []),
            position=_int_or_none(data.get("position")),
            reason=stringify(data.get("reason")),
            sources=list(data.get("sources") or []),
            confidence=_int(data.get("confidence"), 0),
            observation_mode=mode,
            status=str(data.get("status") or mode),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "query_type": self.query_type,
            "company_mentioned": self.company_mentioned,
            "company_recommended": self.company_recommended,
            "company_correctly_described": self.company_correctly_described,
            "company_cited": self.company_cited,
            "competitors_mentioned": self.competitors_mentioned,
            "position": self.position,
            "reason": self.reason,
            "sources": self.sources,
            "confidence": self.confidence,
            "observation_mode": self.observation_mode,
            "status": self.status,
        }


def _int(value: Any, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _int_or_none(value: Any) -> int | None:
    try:
        return None if is_unknown(value) else int(value)
    except (TypeError, ValueError):
        return None
