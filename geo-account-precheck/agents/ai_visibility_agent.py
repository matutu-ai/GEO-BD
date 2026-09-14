"""Build an AI visibility diagnosis from real AI observations only."""

from __future__ import annotations

from typing import Any


UNKNOWN = "【需企业提供真实佐证】"
REAL_MODES = {"observed", "provided"}


class AIVisibilityAgent:
    """Translate existing AI observations into a staged visibility result."""

    def build(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        observations = _real_observations(diagnostic)
        if not observations:
            return {
                "brand_recognition": None,
                "business_understanding": None,
                "trust_level": None,
                "recommend_probability": None,
                "visibility_stage": "UNKNOWN",
                "issues": [UNKNOWN],
            }

        mention = _rate(observations, "company_mentioned")
        understanding = _rate(observations, "company_correctly_described")
        trust = _rate(observations, "company_cited")
        recommendation = _rate(observations, "company_recommended")
        issues = []
        if mention < 60:
            issues.append("企业在 AI 问题中出现率不足。")
        if understanding < 60:
            issues.append("AI 对企业业务的描述尚不稳定。")
        if trust < 60:
            issues.append("AI 可引用的企业信任依据不足。")
        if recommendation < 60:
            issues.append("AI 推荐概率不足。")
        return {
            "brand_recognition": mention,
            "business_understanding": understanding,
            "trust_level": trust,
            "recommend_probability": recommendation,
            "visibility_stage": _stage(mention, understanding, trust, recommendation),
            "issues": issues or ["当前真实观察未发现明显可归纳问题；仍需持续复测。"],
        }


def _real_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in (diagnostic.get("ai_cognition") or {}).get("observations") or []
        if str(item.get("status") or item.get("observation_mode") or "").lower() in REAL_MODES
    ]


def _rate(observations: list[dict[str, Any]], field: str) -> int:
    return round(100 * sum(bool(item.get(field)) for item in observations) / len(observations))


def _stage(mention: int, understanding: int, trust: int, recommendation: int) -> str:
    if recommendation >= 60:
        return "RECOMMEND"
    if trust >= 60:
        return "TRUST"
    if understanding >= 60:
        return "UNDERSTAND"
    if mention >= 20:
        return "KNOWN"
    return "UNKNOWN"
