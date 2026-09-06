"""Before/after diagnostic report comparison."""

from __future__ import annotations

from typing import Any

from ..common import clamp

SCORE_KEYS = [
    ("entity_score", "Entity"),
    ("ai_cognition_score", "AI Cognition"),
    ("evidence_score", "Evidence"),
    ("eeaap_score", "EEAAP"),
    ("eeat_score", "EEAT"),
    ("competitor_gap_score", "Competitor Gap"),
    ("citation_score", "Citation"),
    ("trust_score", "Trust"),
    ("scenario_coverage_score", "Scenario Score"),
    ("keyword_coverage_score", "Keyword Score"),
    ("nap_score", "NAP Score"),
    ("geo_score", "GEO Score"),
]


def compare_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare two diagnostic reports; missing sides never become fabricated numbers."""
    before_scores = before.get("scores") or {}
    after_scores = after.get("scores") or {}
    modules: list[dict[str, Any]] = []
    numeric_deltas: list[float] = []
    for key, label in SCORE_KEYS:
        previous = _number(before_scores.get(key))
        current = _number(after_scores.get(key))
        delta = _delta(previous, current)
        if delta is not None:
            numeric_deltas.append(delta)
        modules.append(
            {
                "metric": label,
                "before": previous,
                "after": current,
                "delta": delta,
                "status": _change_status(delta),
            }
        )

    coverage_before = _coverage(before)
    coverage_after = _coverage(after)
    rate_keys = ("mention_rate", "recommendation_rate", "citation_rate")
    for key in rate_keys:
        previous = _number(coverage_before.get(key)) if coverage_before.get("status") == "OBSERVED" else None
        current = _number(coverage_after.get(key)) if coverage_after.get("status") == "OBSERVED" else None
        delta = _delta(previous, current)
        if delta is not None:
            numeric_deltas.append(delta)
        modules.append(
            {
                "metric": key,
                "before": previous,
                "after": current,
                "delta": delta,
                "status": _change_status(delta),
            }
        )

    scenario_before = _scenario_coverage(before)
    scenario_after = _scenario_coverage(after)
    for label, previous, current in (
        ("Scenario Coverage", scenario_before, scenario_after),
        ("Evidence Count", _evidence_count(before), _evidence_count(after)),
        ("Action Plan Count", _action_count(before), _action_count(after)),
    ):
        delta = _delta(previous, current)
        if delta is not None:
            numeric_deltas.append(delta)
        modules.append(
            {
                "metric": label,
                "before": previous,
                "after": current,
                "delta": delta,
                "status": _change_status(delta),
            }
        )

    resolved = _resolved_gaps(before, after)
    new_evidence = max(_evidence_count(after) - _evidence_count(before), 0)
    improvement_rate = clamp(sum(numeric_deltas) / len(numeric_deltas) + 50) if numeric_deltas else None
    return {
        "status": "COMPUTED" if improvement_rate is not None else "INSUFFICIENT_DATA",
        "improvement_rate": improvement_rate,
        "geo_score_change": _delta(_number(before_scores.get("geo_score")), _number(after_scores.get("geo_score"))),
        "modules": modules,
        "problem_resolution": {
            "resolved_count": resolved,
            "basis": f"{resolved} 个原报告 Gap 在复测中不再出现；其余 Gap 需要继续核验。" if resolved else "没有可确认的 Gap 被消除，或 Before/After 数据不完整。",
        },
        "new_evidence": new_evidence,
        "scenario_coverage_change": _delta(scenario_before, scenario_after),
        "mention_change": _delta(
            _number(coverage_before.get("mention_rate")) if coverage_before.get("status") == "OBSERVED" else None,
            _number(coverage_after.get("mention_rate")) if coverage_after.get("status") == "OBSERVED" else None,
        ),
        "recommendation_change": _delta(
            _number(coverage_before.get("recommendation_rate")) if coverage_before.get("status") == "OBSERVED" else None,
            _number(coverage_after.get("recommendation_rate")) if coverage_after.get("status") == "OBSERVED" else None,
        ),
        "citation_change": _delta(
            _number(coverage_before.get("citation_rate")) if coverage_before.get("status") == "OBSERVED" else None,
            _number(coverage_after.get("citation_rate")) if coverage_after.get("status") == "OBSERVED" else None,
        ),
    }


def _coverage(report: dict[str, Any]) -> dict[str, Any]:
    return (report.get("query_matrix") or {}).get("coverage") or {}


def _scenario_coverage(report: dict[str, Any]) -> float | None:
    coverage = _coverage(report)
    if coverage.get("status") == "OBSERVED":
        return _number(coverage.get("scenario_coverage"))
    summary = report.get("scenarios") or {}
    return _number(summary.get("scenario_coverage"))


def _evidence_count(report: dict[str, Any]) -> int:
    return len((report.get("evidence_graph") or {}).get("items") or [])


def _action_count(report: dict[str, Any]) -> int:
    return len((report.get("recommendations") or {}).get("actions") or [])


def _resolved_gaps(before: dict[str, Any], after: dict[str, Any]) -> int:
    before_gaps = {item.get("type") for item in (before.get("gaps") or {}).get("gaps") or []}
    after_gaps = {item.get("type") for item in (after.get("gaps") or {}).get("gaps") or []}
    return len(before_gaps - after_gaps)


def _delta(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    return round(after - before, 2)


def _change_status(delta: float | None) -> str:
    if delta is None:
        return "NOT_COMPARABLE"
    if delta > 0:
        return "improved"
    if delta < 0:
        return "declined"
    return "unchanged"


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
