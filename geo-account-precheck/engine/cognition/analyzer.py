"""AI Cognition Analyzer."""

from __future__ import annotations

from typing import Any

from ..common import UNKNOWN
from ..models.cognition import AIObservation
from ..models.company import CompanyProfile
from ..models.entity import EntityProfile
from ..query.intent import classify_query
from ..query.matrix import QueryMatrix


class CognitionAnalyzer:
    def __init__(self, company: CompanyProfile, entity: EntityProfile) -> None:
        self.company = company
        self.entity = entity
        self.aliases = [name for name in [company.name, *company.aliases] if name]

    def analyze(
        self,
        observations: list[AIObservation],
        query_matrix: QueryMatrix | None = None,
    ) -> dict[str, Any]:
        parsed: list[AIObservation] = []
        for observation in observations:
            if not observation.query:
                continue
            if observation.query_type == "unknown":
                observation.query_type = classify_query(observation.query)
            parsed.append(observation)

        real_observations = [
            item for item in parsed if item.status in {"observed", "provided"}
        ]
        simulated = [item for item in parsed if item.status == "simulated"]
        coverage = query_matrix.coverage(real_observations) if query_matrix else None
        if coverage and coverage.status == "OBSERVED" and coverage.score is not None:
            status = "OBSERVED"
            score = coverage.score
            basis = "基于真实 AI 观察结果的综合认知评分。"
        else:
            status = UNKNOWN
            score = None
            basis = (
                "只有模拟或未知观察结果，不把模拟结果写成真实认知评分。"
                if simulated
                else "未提供真实 AI 观察结果，不假装 AI 认知评分。"
            )

        return {
            "observation_mode": _observation_mode(parsed, real_observations, simulated),
            "status": status,
            "score": score,
            "observations": [item.to_dict() for item in parsed],
            "count": len(parsed),
            "basis": basis,
        }

    @staticmethod
    def observations_from_input(data: dict[str, Any], company: CompanyProfile) -> list[AIObservation]:
        observations = [AIObservation.from_dict(item) for item in (data.get("ai_observations") or [])]
        for observation in observations:
            if observation.observation_mode not in {"observed", "provided", "simulated"}:
                observation.observation_mode = (
                    observation.status
                    if observation.status in {"observed", "provided", "simulated"}
                    else UNKNOWN
                )
            observation.status = observation.observation_mode
        return observations


def _observation_mode(
    parsed: list[AIObservation],
    real: list[AIObservation],
    simulated: list[AIObservation],
) -> str:
    if real and simulated:
        return "mixed"
    if real:
        return "observed" if any(item.status == "observed" for item in real) else "provided"
    if simulated:
        return "simulated"
    return UNKNOWN if not parsed else "unknown"
