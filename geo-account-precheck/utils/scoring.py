"""GEO growth score based on the V3 diagnosis handoff dimensions."""

from __future__ import annotations

from typing import Any

from engine.common import clamp


WEIGHTS = {
    "ai_visibility": 0.30,
    "positioning": 0.20,
    "eeat": 0.30,
    "content": 0.20,
}


def calculate_geo_score(
    diagnostic: dict[str, Any],
    ai_visibility: dict[str, Any],
    eeat_score: dict[str, Any],
    geo_gap: dict[str, Any],
) -> dict[str, Any]:
    dimensions = {
        "ai_visibility": _visibility_score(ai_visibility),
        "positioning": _number((diagnostic.get("scores") or {}).get("entity_score")),
        "eeat": _number(eeat_score.get("total")),
        "content": _content_score(diagnostic, geo_gap),
    }
    available = [(WEIGHTS[key], value) for key, value in dimensions.items() if value is not None]
    total = None
    if available:
        total = clamp(sum(weight * value for weight, value in available) / sum(weight for weight, _ in available))
    return {
        "total": total,
        "status": "COMPUTED" if total is not None else "INSUFFICIENT_DATA",
        "dimensions": dimensions,
        "weights": WEIGHTS,
        "stage": _stage(total),
        "basis": "AI Visibility 30%、Positioning 20%、EEAT 30%、Content 20%；缺失维度不按 0 计入。",
    }


def _visibility_score(result: dict[str, Any]) -> int | None:
    values = [result.get(key) for key in (
        "brand_recognition", "business_understanding", "trust_level", "recommend_probability"
    )]
    numbers = [_number(value) for value in values if _number(value) is not None]
    return clamp(sum(numbers) / len(numbers)) if len(numbers) == 4 else None


def _content_score(diagnostic: dict[str, Any], gap_result: dict[str, Any]) -> int | None:
    scores = diagnostic.get("scores") or {}
    coverage_scores = [
        _number(scores.get("scenario_coverage_score")),
        _number(scores.get("keyword_coverage_score")),
    ]
    coverage_scores = [value for value in coverage_scores if value is not None]
    if coverage_scores:
        return clamp(sum(coverage_scores) / len(coverage_scores))

    gaps = gap_result.get("gaps") or []
    candidates = [
        100 - _gap_score(item)
        for item in gaps
        if str(item.get("problem")) == "产品与专业表达不足" and _gap_score(item) is not None
    ]
    return clamp(candidates[0]) if candidates else None


def _gap_score(item: dict[str, Any]) -> int | None:
    reason = str(item.get("reason") or "")
    for token in ("/100", "分数"):
        if token in reason:
            before = reason.split(token, 1)[0].split()[-1]
            try:
                return int(before)
            except ValueError:
                continue
    return None


def _stage(total: int | None) -> str:
    if total is None:
        return "UNKNOWN"
    if total >= 90:
        return "AI推荐阶段"
    if total >= 70:
        return "AI理解阶段"
    if total >= 40:
        return "AI识别阶段"
    return "未知阶段"


def _number(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return clamp(float(value))
    except (TypeError, ValueError):
        return None
