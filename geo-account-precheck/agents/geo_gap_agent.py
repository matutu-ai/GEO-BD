"""Convert engine gaps into a compact AI growth gap map."""

from __future__ import annotations

from typing import Any


UNKNOWN = "【需企业提供真实佐证】"


class GEOGapAgent:
    """Map existing diagnostic gaps to positioning and growth problem categories."""

    def build(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        gaps = (diagnostic.get("gaps") or {}).get("gaps") or []
        output = [mapped for item in gaps if (mapped := _map_gap(item)) is not None]
        if not output:
            output = [{
                "problem": "诊断缺口未知",
                "reason": UNKNOWN,
                "impact": UNKNOWN,
                "priority": "P0",
            }]
        return {"gaps": output}


def _map_gap(gap: dict[str, Any]) -> dict[str, Any] | None:
    if int(gap.get("score") or 0) <= 0:
        return None
    gap_type = str(gap.get("type") or "Unknown Gap")
    problem, priority = {
        "Entity Gap": ("企业定位与公开信息待校准", "P0"),
        "Query Gap": ("用户需求场景不足", "P1"),
        "Evidence Gap": ("信任证明不足", "P1"),
        "Experience Gap": ("案例经验不足", "P1"),
        "Authority Gap": ("权威背书不足", "P1"),
        "Content Gap": ("产品与专业表达不足", "P2"),
        "Citation Gap": ("AI 可引用来源不足", "P1"),
        "Trust Gap": ("企业信任信息不足", "P1"),
        "Local/NAP Gap": ("企业公开信息一致性不足", "P0"),
        "Competitor Gap": ("竞争认知差距待确认", "P2"),
    }.get(gap_type, (gap_type, "P2"))
    reason = str(gap.get("reason") or UNKNOWN)
    return {
        "problem": problem,
        "reason": reason,
        "impact": _impact(priority, reason),
        "priority": priority,
    }


def _impact(priority: str, reason: str) -> str:
    if UNKNOWN in reason:
        return UNKNOWN
    return {
        "P0": "AI 难以形成稳定的企业实体认知。",
        "P1": "AI 缺少理解、信任或推荐企业的依据。",
        "P2": "企业专业价值和竞争差异难以被持续识别。",
    }.get(priority, "影响需要结合真实资料进一步确认。")
