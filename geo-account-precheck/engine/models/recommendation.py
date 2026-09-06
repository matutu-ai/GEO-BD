"""Recommendation action model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecommendationAction:
    task: str = ""
    priority: str = "P2"
    problem: str = ""
    why: str = ""
    evidence: list[str] = field(default_factory=list)
    impact: list[str] = field(default_factory=list)
    action: str = ""
    required_materials: list[str] = field(default_factory=list)
    verification: str = ""
    source_doc_heuristics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "priority": self.priority,
            "problem": self.problem,
            "why": self.why,
            "evidence": self.evidence,
            "impact": self.impact,
            "action": self.action,
            "required_materials": self.required_materials,
            "verification": self.verification,
            "source_doc_heuristics": self.source_doc_heuristics,
        }
