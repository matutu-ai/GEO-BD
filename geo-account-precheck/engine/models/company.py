"""Company-level input model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import is_unknown, listify, stringify


@dataclass
class CompanyProfile:
    name: str = ""
    business: str = ""
    industry: list[str] = field(default_factory=list)
    customers: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    materials: list[Any] = field(default_factory=list)
    ai_observations: list[dict[str, Any]] = field(default_factory=list)
    competitors: list[Any] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    keyword_directions: list[str] = field(default_factory=list)
    queries: list[dict[str, Any]] = field(default_factory=list)
    current_metrics: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompanyProfile":
        company = data.get("company") or {}
        if isinstance(company, str):
            company = {"name": company}
        nested = company if isinstance(company, dict) else {}
        name = stringify(nested.get("name") or data.get("company") or data.get("company_name"))
        return cls(
            name=name,
            business=stringify(nested.get("business") or data.get("business")),
            industry=listify(nested.get("industry") or data.get("industry")),
            customers=listify(nested.get("customers") or data.get("customers")),
            locations=listify(nested.get("locations") or data.get("locations")),
            aliases=listify(nested.get("aliases") or data.get("aliases")),
            materials=listify(data.get("materials")),
            ai_observations=list(data.get("ai_observations") or []),
            competitors=list(data.get("competitors") or []),
            evidence=list(data.get("evidence") or []),
            issues=listify(data.get("issues")),
            keyword_directions=listify(data.get("keyword_directions")),
            queries=list(data.get("queries") or data.get("query_matrix") or []),
            current_metrics=dict(data.get("current_metrics") or {}),
            validation=dict(data.get("validation") or {}),
            constraints=dict(data.get("constraints") or {}),
            raw=data,
        )

    @property
    def has_basics(self) -> bool:
        return bool(self.name and self.business and not is_unknown(self.name))
