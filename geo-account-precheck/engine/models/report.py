"""Final diagnostic report container."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import to_dict


@dataclass
class DiagnosticResult:
    meta: dict[str, Any] = field(default_factory=dict)
    company: dict[str, Any] = field(default_factory=dict)
    entity: dict[str, Any] = field(default_factory=dict)
    ai_cognition: dict[str, Any] = field(default_factory=dict)
    query_matrix: dict[str, Any] = field(default_factory=dict)
    competitors: dict[str, Any] = field(default_factory=dict)
    evidence_graph: dict[str, Any] = field(default_factory=dict)
    eeaap: dict[str, Any] = field(default_factory=dict)
    eeat: dict[str, Any] = field(default_factory=dict)
    gaps: dict[str, Any] = field(default_factory=dict)
    opportunities: dict[str, Any] = field(default_factory=dict)
    recommendations: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    scores: dict[str, Any] = field(default_factory=dict)
    data_quality: dict[str, Any] = field(default_factory=dict)
    scenarios: dict[str, Any] = field(default_factory=dict)
    keywords: dict[str, Any] = field(default_factory=dict)
    citations: dict[str, Any] = field(default_factory=dict)
    nap: dict[str, Any] = field(default_factory=dict)
    ai_tests: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)
