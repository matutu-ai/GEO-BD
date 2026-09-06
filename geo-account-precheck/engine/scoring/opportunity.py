"""Opportunity scoring and P0/P1/P2/P3 generation."""

from __future__ import annotations

from typing import Any

from ..common import INFERENCE, clamp
from ..models.scoring import Opportunity

TITLES = {
    "Entity Gap": "补齐企业基础实体资料",
    "Query Gap": "为高频推荐 Query 补齐内容",
    "Evidence Gap": "建立可核验证据包",
    "Experience Gap": "补充真实客户案例",
    "Authority Gap": "补充第三方权威证明",
    "Content Gap": "按场景补齐画像内容",
    "Citation Gap": "提升 AI 引用/采信率",
    "Trust Gap": "提升信任基础与来源核验",
    "Local/NAP Gap": "修复全网 NAP 冲突",
    "Competitor Gap": "缩小与竞品的可比差距",
}

FEASIBILITY = {
    "Local/NAP Gap": 90,
    "Experience Gap": 85,
    "Entity Gap": 80,
    "Query Gap": 80,
    "Content Gap": 75,
    "Evidence Gap": 70,
    "Citation Gap": 70,
    "Competitor Gap": 70,
    "Authority Gap": 60,
    "Trust Gap": 65,
}

EVIDENCE_AVAILABILITY = {
    "Local/NAP Gap": 90,
    "Entity Gap": 85,
    "Experience Gap": 80,
    "Query Gap": 75,
    "Evidence Gap": 70,
    "Content Gap": 70,
    "Citation Gap": 60,
    "Trust Gap": 60,
    "Authority Gap": 50,
    "Competitor Gap": 55,
}


class OpportunityScorer:
    def score(
        self,
        gaps: list[dict[str, Any]],
        queries: list[Any],
        current_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        opportunities: list[Opportunity] = []
        for gap in gaps:
            title = TITLES.get(gap["type"], f"优化 {gap['type']}")
            severity = gap["severity"]
            business_value = 95 if severity == "critical" else 85 if severity == "high" else 70
            ai_demand = _ai_demand(gap, queries, current_metrics)
            competitor_gap = _competitor_gap_factor(gap)
            evidence_availability = EVIDENCE_AVAILABILITY.get(gap["type"], 60)
            feasibility = FEASIBILITY.get(gap["type"], 70)
            opportunity_score = _formula_score(
                business_value,
                ai_demand,
                competitor_gap,
                evidence_availability,
                feasibility,
            )
            priority = Opportunity.priority_for(opportunity_score)
            reason = (
                f"{gap['reason']} 该缺口按业务价值/需求强度/竞品差距/证据可得性/执行可行性计算为 "
                f"{opportunity_score}/100，建议{priority}处理。"
            )
            opportunities.append(
                Opportunity(
                    title=title,
                    score=opportunity_score,
                    priority=priority,
                    business_value=business_value,
                    ai_demand=ai_demand,
                    competitor_gap=competitor_gap,
                    evidence_availability=evidence_availability,
                    feasibility=feasibility,
                    reason=reason,
                    status=INFERENCE,
                    basis="机会分数是诊断排序指标，不承诺真实排名变化。",
                )
            )
        opportunities.sort(key=lambda item: item.score, reverse=True)
        return {
            "status": "COMPUTED",
            "opportunities": [item.to_dict() for item in opportunities],
            "count": len(opportunities),
        }


def _ai_demand(gap: dict[str, Any], queries: list[Any], current_metrics: dict[str, Any]) -> int:
    query_demands = [getattr(query, "ai_demand", 0) for query in queries if getattr(query, "ai_demand", 0)]
    metric = current_metrics.get("ai_demand") or current_metrics.get("search_demand")
    try:
        metric_value = clamp(float(metric)) if metric not in (None, "") else None
    except (TypeError, ValueError):
        metric_value = None
    candidates = [value for value in [*query_demands, metric_value] if value is not None]
    if candidates:
        return clamp(sum(candidates) / len(candidates))
    if gap["severity"] in {"critical", "high"}:
        return 80
    return 60


def _competitor_gap_factor(gap: dict[str, Any]) -> int:
    measured_gap = clamp(gap.get("score", 0) or 0)
    severity_minimum = {
        "critical": 90,
        "high": 75,
        "medium": 55,
        "low": 35,
    }
    return max(measured_gap, severity_minimum.get(str(gap.get("severity")), 40))


def _formula_score(
    business_value: int,
    ai_demand: int,
    competitor_gap: int,
    evidence_availability: int,
    feasibility: int,
) -> int:
    product = (
        business_value
        * ai_demand
        * competitor_gap
        * evidence_availability
        * feasibility
    )
    return clamp(product ** (1 / 5))
