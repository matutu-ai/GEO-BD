"""Query matrix construction and coverage calculation."""

from __future__ import annotations

from typing import Any

from ..common import INFERENCE, clamp, is_unknown
from ..models.company import CompanyProfile
from ..models.query import Query, QueryCoverage
from .intent import classify_query


class QueryMatrix:
    def __init__(self, queries: list[Query] | None = None) -> None:
        self.queries = list(queries or [])

    def build(self, profile: CompanyProfile) -> "QueryMatrix":
        raw_queries = profile.raw.get("queries") or profile.raw.get("query_matrix") or profile.queries
        parsed = [_query_from_dict(item) if isinstance(item, dict) else _query_from_text(str(item)) for item in raw_queries]
        parsed = [query for query in parsed if query.query]

        for direction in profile.keyword_directions:
            parsed.append(_query_from_text(direction, intent="scenario"))

        if not parsed and profile.business and not is_unknown(profile.business):
            parsed = self._infer_candidates(profile)

        self.queries = _dedupe(parsed)
        return self

    def to_dict(self, coverage: QueryCoverage | None = None) -> dict[str, Any]:
        return {
            "total": len(self.queries),
            "status": "GENERATED" if self.queries else "UNKNOWN",
            "queries": [query.to_dict() for query in self.queries],
            "coverage": (coverage or self.coverage([])).to_dict(),
        }

    def coverage(self, observations: list[Any]) -> QueryCoverage:
        real = [
            item
            for item in observations
            if _observation_status(item) in {"observed", "provided"}
        ]
        ignored = len(observations) - len(real)
        total = len(real)
        if not total:
            return QueryCoverage(
                total=0,
                status="UNKNOWN",
                basis=(
                    "只有模拟或未知观察结果，不把模拟结果计为真实覆盖。"
                    if ignored
                    else "没有真实 AI 观察结果，Query Coverage 暂不评分。"
                ),
            )
        mentioned = sum(1 for item in real if item.company_mentioned)
        recommended = sum(1 for item in real if item.company_recommended)
        described = sum(1 for item in real if item.company_correctly_described)
        cited = sum(1 for item in real if item.company_cited)
        unique_types = {item.query_type for item in real if item.query_type and item.query_type != "unknown"}

        mention_rate = mentioned / total
        recommendation_rate = recommended / total
        description_accuracy = described / total
        citation_rate = cited / total
        scenario_coverage = len(unique_types) / max(total, 1) if unique_types else 0.0
        score = clamp(
            100
            * (
                0.25 * mention_rate
                + 0.30 * recommendation_rate
                + 0.20 * description_accuracy
                + 0.10 * citation_rate
                + 0.15 * scenario_coverage
            )
        )
        result = QueryCoverage(
            total=total,
            mentioned=mentioned,
            recommended=recommended,
            correctly_described=described,
            cited=cited,
            mention_rate=round(mention_rate * 100),
            recommendation_rate=round(recommendation_rate * 100),
            description_accuracy=round(description_accuracy * 100),
            citation_rate=round(citation_rate * 100),
            scenario_coverage=round(scenario_coverage * 100),
            score=score,
            status="OBSERVED",
            basis="依据用户提供的真实 AI 观察结果计算。",
        )
        if ignored:
            result.basis = f"依据真实 AI 观察结果计算；另有 {ignored} 条模拟/未知观察不计分。"
        return result

    def _infer_candidates(self, profile: CompanyProfile) -> list[Query]:
        business = profile.business
        candidates: list[Query] = []
        industries = "、".join(profile.industry) if profile.industry else business
        if industries:
            candidates.append(
                _query_from_text(f"{industries}有哪些值得推荐的公司", intent="recommendation")
            )
            candidates.append(_query_from_text(f"{business}怎么选", intent="decision"))
        for customer in profile.customers[:6]:
            candidates.append(
                _query_from_text(f"{customer}使用的{business}怎么选", intent="scenario")
            )
        for location in profile.locations[:6]:
            candidates.append(
                _query_from_text(f"{location}{business}厂家推荐", intent="local")
            )
        return candidates


def _query_from_text(text: str, intent: str | None = None) -> Query:
    text = text.strip()
    return Query(
        query=text,
        intent=intent or classify_query(text),
        root=text,
        scenario=text,
        status=INFERENCE,
        source="输入关键词/引擎候选模板",
    )


def _query_from_dict(data: dict[str, Any]) -> Query:
    text = str(data.get("query") or data.get("keyword") or "").strip()
    if not text:
        return Query(status=INFERENCE, source="输入关键词")
    intent = classify_query(text, bool(data.get("company_mentioned", False)))
    return Query(
        query=text,
        intent=str(data.get("intent") or intent),
        root=str(data.get("root") or text),
        scenario=str(data.get("scenario") or text),
        industry=str(data.get("industry") or ""),
        location=str(data.get("location") or ""),
        demand=str(data.get("demand") or ""),
        pain_point=str(data.get("pain_point") or ""),
        business_value=_int(data.get("business_value"), 0),
        ai_demand=_int(data.get("ai_demand"), 0),
        status=str(data.get("status") or INFERENCE),
        source=str(data.get("source") or "用户提供"),
    )


def _observation_status(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("status") or "observed")
    return str(getattr(item, "status", "observed") or "observed")


def _dedupe(queries: list[Query]) -> list[Query]:
    seen: set[str] = set()
    result: list[Query] = []
    for query in queries:
        if query.query in seen:
            continue
        seen.add(query.query)
        result.append(query)
    return result


def _int(value: Any, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default
