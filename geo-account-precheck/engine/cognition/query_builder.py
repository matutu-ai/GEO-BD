"""Standard AI cognition question bank."""

from __future__ import annotations

from typing import Any

from ..common import is_unknown
from ..models.company import CompanyProfile
from ..models.entity import EntityProfile


def build_cognition_queries(company: CompanyProfile, entity: EntityProfile) -> list[dict[str, str]]:
    queries: list[dict[str, str]] = []
    name = company.name or entity.get_value("name")
    business = company.business or entity.get_value("business")

    if name:
        queries.extend(
            [
                {"query": f"{name}是做什么的", "query_type": "brand"},
                {"query": f"{name}主营什么", "query_type": "brand"},
                {"query": f"{name}有哪些产品", "query_type": "product"},
                {"query": f"{name}有什么核心优势", "query_type": "brand"},
                {"query": f"{name}最核心优势是什么", "query_type": "brand"},
                {"query": f"{name}靠谱吗", "query_type": "decision"},
            ]
        )
    if business:
        industries = "、".join(company.industry or entity.get_values("industry")) or business
        queries.append({"query": f"{industries}有哪些值得推荐的公司", "query_type": "recommendation"})
        queries.append({"query": f"{business}应该怎么选", "query_type": "decision"})
    for location in company.locations or entity.get_values("locations"):
        if business:
            queries.append({"query": f"{location}有哪些靠谱的{business}厂家", "query_type": "local"})

    if name and not is_unknown(business):
        queries.append({"query": f"{name}的产品和方案适合什么客户", "query_type": "scenario"})
    return queries
