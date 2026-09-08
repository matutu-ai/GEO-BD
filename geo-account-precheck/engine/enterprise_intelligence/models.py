"""Dataclasses for enterprise intelligence and conditional recommendation output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import to_dict


@dataclass
class CompanyIntelligence:
    company_name: str = ""
    legal_name: str = ""
    location: str = ""
    founded_year: Any = None
    registered_capital: Any = None
    industry: list[str] = field(default_factory=list)
    business_model: list[str] = field(default_factory=list)
    primary_business: list[str] = field(default_factory=list)
    secondary_business: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    target_customers: list[str] = field(default_factory=list)
    target_regions: list[str] = field(default_factory=list)
    application_scenarios: list[str] = field(default_factory=list)
    manufacturing_capabilities: list[str] = field(default_factory=list)
    technology_capabilities: list[str] = field(default_factory=list)
    project_experience: list[str] = field(default_factory=list)
    brand_attributes: list[str] = field(default_factory=list)
    known_constraints: list[str] = field(default_factory=list)
    unknown_items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class Capability:
    capability: str = ""
    type: str = ""
    level: int = 0
    evidence: list[str] = field(default_factory=list)
    confidence: int = 0
    regions: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class QualificationBoundary:
    item: str = ""
    type: str = "qualification"
    status: str = "unknown"
    evidence: list[str] = field(default_factory=list)
    risk_level: str = "medium"
    allowed_claims: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    recommended_disclosure: str = ""

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class EvidenceReview:
    id: str = ""
    claim: str = ""
    source: str = ""
    source_type: str = "unknown"
    tier: int = 5
    date: str = ""
    region: str = ""
    evidence_strength: int = 0
    verification_status: str = "unknown"
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class CompetitorPool:
    pool: str = ""
    relationship: str = "not_competitor"
    members: list[str] = field(default_factory=list)
    basis: str = ""
    client_advantage: list[str] = field(default_factory=list)
    client_disadvantage: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class CustomerScenario:
    scenario: str = ""
    customer_type: str = ""
    need: str = ""
    product_match: int = 0
    capability_match: int = 0
    qualification_match: int = 0
    regional_match: int = 0
    evidence_strength: int = 0
    recommendation_score: int = 0
    recommended: bool = False
    reason: str = ""
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class RecommendationDecision:
    query: str = ""
    intent: str = ""
    match: str = ""
    recommendation: str = ""
    score: int = 0
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    product_match: int = 0
    capability_match: int = 0
    qualification_match: int = 0
    regional_match: int = 0
    evidence_strength: int = 0

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class Positioning:
    primary_positioning: str = ""
    secondary_positioning: list[str] = field(default_factory=list)
    core_tags: list[str] = field(default_factory=list)
    regional_tags: list[str] = field(default_factory=list)
    product_authority: list[str] = field(default_factory=list)
    service_authority: list[str] = field(default_factory=list)
    recommended_customer_types: list[str] = field(default_factory=list)
    recommended_scenarios: list[str] = field(default_factory=list)
    restricted_scenarios: list[str] = field(default_factory=list)
    competitive_position: str = ""
    one_sentence_positioning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class PromotionStrategy:
    promote: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    priorities: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class GeoContentGap:
    gap_type: str = ""
    severity: str = "medium"
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class ClaimSafety:
    claim: str = ""
    status: str = "UNKNOWN"
    evidence: list[str] = field(default_factory=list)
    reason: str = ""
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)


@dataclass
class CompetitionIntelligence:
    company_intelligence: CompanyIntelligence = field(default_factory=CompanyIntelligence)
    capabilities: list[Capability] = field(default_factory=list)
    qualification_boundary: list[QualificationBoundary] = field(default_factory=list)
    evidence_review: list[EvidenceReview] = field(default_factory=list)
    competitor_pools: list[CompetitorPool] = field(default_factory=list)
    customer_scenarios: list[CustomerScenario] = field(default_factory=list)
    recommendation_decisions: list[RecommendationDecision] = field(default_factory=list)
    query_summary: dict[str, Any] = field(default_factory=dict)
    positioning: Positioning = field(default_factory=Positioning)
    promotion_strategy: PromotionStrategy = field(default_factory=PromotionStrategy)
    geo_content_gaps: list[GeoContentGap] = field(default_factory=list)
    claim_safety: list[ClaimSafety] = field(default_factory=list)
    recommendation_status: str = "COMPUTED"
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)
