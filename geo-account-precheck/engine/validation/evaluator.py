"""Validation evaluator for pre/post optimization measurement."""

from __future__ import annotations

from typing import Any

from ..common import UNKNOWN, clamp

METRICS = [
    "mention_rate",
    "recommendation_rate",
    "query_coverage",
    "citation_rate",
    "brand_recognition",
    "product_recognition",
    "evidence_score",
    "eeaap",
    "eeat",
    "geo_opportunity",
]


class ValidationEvaluator:
    def evaluate(self, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        if not after:
            return {
                "status": UNKNOWN,
                "improvement_score": None,
                "basis": "没有真实复测数据，不能输出 Improved/Declined。",
                "metric_changes": [],
            }

        changes: list[dict[str, Any]] = []
        for metric in METRICS:
            before_value = _number(before.get(metric))
            after_value = _number(after.get(metric))
            if before_value is None or after_value is None:
                continue
            delta = after_value - before_value
            changes.append(
                {
                    "metric": metric,
                    "before": before_value,
                    "after": after_value,
                    "delta": delta,
                    "status": "improved" if delta > 0 else "unchanged" if delta == 0 else "declined",
                }
            )
        if not changes:
            return {
                "status": UNKNOWN,
                "improvement_score": None,
                "basis": "复测数据存在但没有可比较的核心指标。",
                "metric_changes": [],
            }

        deltas = [change["delta"] for change in changes]
        average_delta = sum(deltas) / len(deltas)
        improvement_score = clamp(50 + average_delta / 2)
        if average_delta > 0.5:
            status = "Improved"
        elif average_delta < -0.5:
            status = "Declined"
        else:
            status = "Unchanged"
        return {
            "status": status,
            "improvement_score": improvement_score,
            "basis": f"比较 {len(changes)} 个核心指标，平均变化 {average_delta:+.1f}。",
            "metric_changes": changes,
        }


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
