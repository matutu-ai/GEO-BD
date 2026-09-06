"""Real AI test analysis: mention/recommendation/citation metrics."""

from __future__ import annotations

from typing import Any

from ..common import clamp

REAL_MODES = {"observed", "provided"}


def analyze_ai_tests(tests: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute rates from real AI answers. Missing or simulated tests stay NOT_RUN."""
    real = [
        item
        for item in tests
        if str(item.get("status") or item.get("observation_mode") or "provided") in REAL_MODES
    ]
    if not real:
        return {
            "status": "NOT_RUN",
            "insufficient_data": True,
            "basis": "没有真实 AI 测试结果；不计算 Mention/Recommendation/Citation 数字。",
            "total": 0,
            "mention_rate": None,
            "recommendation_rate": None,
            "citation_rate": None,
            "average_position": None,
            "competitor_presence": [],
            "results": [],
        }

    mentioned = sum(1 for item in real if bool(item.get("company_mentioned", False)))
    recommended = sum(1 for item in real if bool(item.get("company_recommended", False)))
    cited = sum(1 for item in real if bool(item.get("company_cited", False)))
    positions = [_number(item.get("position")) for item in real]
    positions = [value for value in positions if value is not None]
    competitors: list[str] = []
    for item in real:
        for name in item.get("competitors_mentioned") or []:
            if name not in competitors:
                competitors.append(str(name))

    return {
        "status": "COMPUTED",
        "insufficient_data": False,
        "basis": "基于真实 AI 测试回答计算。",
        "total": len(real),
        "mention_rate": clamp(100 * mentioned / len(real)),
        "recommendation_rate": clamp(100 * recommended / len(real)),
        "citation_rate": clamp(100 * cited / len(real)),
        "average_position": round(sum(positions) / len(positions), 2) if positions else None,
        "competitor_presence": competitors,
        "results": [dict(item) for item in real],
    }


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
