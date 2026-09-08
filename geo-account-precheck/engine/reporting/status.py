"""Shared status vocabulary for the V3 report layer.

Statuses describe how a value was obtained. They never turn an estimate into an
observation, and an empty dataset must stay UNKNOWN instead of becoming zero.
"""

from __future__ import annotations

from typing import Any

OBSERVED = "OBSERVED"
PROVIDED = "PROVIDED"
DERIVED = "DERIVED"
ESTIMATED = "ESTIMATED"
UNKNOWN = "UNKNOWN"
CONFLICT = "CONFLICT"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
NOT_RUN = "NOT_RUN"
NONE = "NONE"
WARNING = "WARNING"
PASS = "PASS"

STATUS_LABELS = {
    OBSERVED: "真实 AI 测试得到",
    PROVIDED: "用户提供",
    DERIVED: "由可信数据计算",
    ESTIMATED: "模型估算",
    UNKNOWN: "没有足够数据",
    CONFLICT: "不同来源存在冲突",
    INSUFFICIENT_DATA: "数据不足以形成结论",
    NOT_RUN: "尚未执行真实测试",
    NONE: "未发现",
    WARNING: "需要核验",
    PASS: "通过",
}

SCORE_BANDS = (
    (90, "优秀", "优秀 · 已具备较完整的可观察证据基础"),
    (75, "良好", "良好 · 有明显增长空间"),
    (60, "中等", "中等 · 有明显增长空间"),
    (40, "偏弱", "偏弱 · 需要补齐关键证据与认知"),
    (0, "严重不足", "严重不足 · 需要从基础资料与真实观察开始补齐"),
)


def metric(value: Any, status: str, basis: str, unit: str = "") -> dict[str, Any]:
    """Build one traceable report metric."""
    return {"value": value, "status": status, "basis": basis, "unit": unit}


def score_band(score: int | None) -> tuple[str, str] | None:
    if score is None:
        return None
    for threshold, band, label in SCORE_BANDS:
        if score >= threshold:
            return band, label
    return None


def confidence_label(confidence: float | None) -> str:
    if confidence is None:
        return UNKNOWN
    if confidence >= 0.85:
        return "高可信"
    if confidence >= 0.65:
        return "中高可信"
    if confidence >= 0.5:
        return "中等可信"
    return "低可信"


def priority_for(score: int | None) -> str:
    if score is None:
        return "P3"
    if score >= 75:
        return "P0"
    if score >= 55:
        return "P1"
    if score >= 35:
        return "P2"
    return "P3"


def impact_stars(impact: int | None) -> str:
    if impact is None:
        return "—"
    filled = max(0, min(5, round(impact / 20)))
    return "★" * filled + "☆" * (5 - filled)
