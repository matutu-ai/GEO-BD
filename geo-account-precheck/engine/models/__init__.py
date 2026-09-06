"""Domain models for the GEO diagnostic engine."""

from .company import CompanyProfile
from .entity import EntityProfile, FactValue
from .query import Query, QueryCoverage
from .competitor import Competitor
from .evidence import EvidenceGraph, EvidenceItem, EvidenceScore
from .cognition import AIObservation
from .gap import GeoGap
from .scoring import Opportunity, ScoreSet
from .recommendation import RecommendationAction
from .report import DiagnosticResult

__all__ = [
    "AIObservation",
    "CompanyProfile",
    "Competitor",
    "DiagnosticResult",
    "EntityProfile",
    "EvidenceGraph",
    "EvidenceItem",
    "EvidenceScore",
    "FactValue",
    "GeoGap",
    "Opportunity",
    "Query",
    "QueryCoverage",
    "RecommendationAction",
    "ScoreSet",
]
