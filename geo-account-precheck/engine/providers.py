"""Provider interfaces for external research and AI observations.

The engine never fabricates results.  When no API/network is available the
pipeline must use ManualProvider or OfflineProvider and keep unknown values
marked as UNKNOWN.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResearchProvider(ABC):
    @abstractmethod
    def research_company(self, company: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def search_evidence(self, company: dict[str, Any], query: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def find_competitors(self, company: dict[str, Any], industry: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class AIObservationProvider(ABC):
    @abstractmethod
    def run_query(self, query: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def batch_run(self, queries: list[str]) -> list[dict[str, Any] | None]:
        return [self.run_query(query) for query in queries]


class SourceVerifier(ABC):
    @abstractmethod
    def verify(self, item: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class ManualProvider(ResearchProvider, AIObservationProvider, SourceVerifier):
    """Provider that only returns data already supplied by the operator."""

    def __init__(self, manual_data: dict[str, Any] | None = None) -> None:
        self.manual_data = manual_data or {}

    def research_company(self, company: dict[str, Any]) -> dict[str, Any]:
        return dict(company)

    def search_evidence(self, company: dict[str, Any], query: str) -> list[dict[str, Any]]:
        return list(self.manual_data.get("search_results") or [])

    def find_competitors(self, company: dict[str, Any], industry: str) -> list[dict[str, Any]]:
        return list(self.manual_data.get("competitors") or [])

    def run_query(self, query: str) -> dict[str, Any] | None:
        for observation in self.manual_data.get("ai_observations") or []:
            if str(observation.get("query")) == query:
                return dict(observation)
        return None

    def batch_run(self, queries: list[str]) -> list[dict[str, Any] | None]:
        return [self.run_query(query) for query in queries]

    def verify(self, item: dict[str, Any]) -> dict[str, Any]:
        return dict(item)


class OfflineProvider(ManualProvider):
    """Offline provider: no external calls, no invented results."""

    def research_company(self, company: dict[str, Any]) -> dict[str, Any]:
        return dict(company)

    def search_evidence(self, company: dict[str, Any], query: str) -> list[dict[str, Any]]:
        return []

    def find_competitors(self, company: dict[str, Any], industry: str) -> list[dict[str, Any]]:
        return []

    def run_query(self, query: str) -> dict[str, Any] | None:
        return None
