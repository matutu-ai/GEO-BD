"""Competitor intelligence and gap matrix analyzer."""

from __future__ import annotations

from typing import Any

from ..common import INFERENCE, UNKNOWN, average_int, clamp
from ..models.competitor import Competitor, CompetitorAnalysis, CompetitorDimensionGap
from ..models.entity import EntityProfile
from ..query.matrix import QueryMatrix

DIMENSION_SOURCES = {
    "品牌认知": "entity",
    "产品认知": "entity",
    "场景认知": "query",
    "地域认知": "local",
    "专家认知": "entity",
    "案例认知": "evidence",
    "Evidence": "evidence",
    "Authority": "authority",
    "Citation": "citation",
    "AI推荐率": "recommendation",
}


class CompetitorAnalyzer:
    def __init__(self, company_name: str) -> None:
        self.company_name = company_name

    def analyze(
        self,
        competitors: list[Competitor],
        entity: EntityProfile,
        client_scores: dict[str, int | None],
        query_matrix: QueryMatrix | None = None,
    ) -> CompetitorAnalysis:
        # User-supplied names stay candidate until confirmed through research.
        clean = [competitor for competitor in competitors if competitor.name and competitor.name != self.company_name]
        if not clean:
            return CompetitorAnalysis(
                status=UNKNOWN,
                basis="未提供可靠竞品数据；不自动制造竞品。",
            )

        matrix: list[CompetitorDimensionGap] = []
        for dimension, source_key in DIMENSION_SOURCES.items():
            client_score = client_scores.get(source_key)
            competitor_scores = [
                _dimension_score(competitor, dimension, source_key)
                for competitor in clean
                if _dimension_score(competitor, dimension, source_key) is not None
            ]
            if client_score is None or not competitor_scores:
                matrix.append(
                    CompetitorDimensionGap(
                        dimension=dimension,
                        client_score=client_score,
                        status=UNKNOWN,
                        basis="缺少客户侧或竞品侧可比数据。",
                    )
                )
                continue
            competitor_score = average_int(competitor_scores)
            gap = clamp(competitor_score - client_score, 0, 100)
            matrix.append(
                CompetitorDimensionGap(
                    dimension=dimension,
                    client_score=client_score,
                    competitor_score=competitor_score,
                    gap=gap,
                    status="COMPUTED",
                    basis="按可比维度的 0-100 指标差计算；数值越小表示竞品优势越小。",
                )
            )

        computed = [entry.gap for entry in matrix if entry.gap is not None]
        score = clamp(100 - average_int(computed)) if computed else None
        return CompetitorAnalysis(
            competitors=clean,
            gap_matrix=matrix,
            score=score,
            status="COMPUTED" if score is not None else UNKNOWN,
            basis=(
                "竞品缺口分数是诊断指标：100 表示未发现可比竞品优势，0 表示竞品在所有可比维度全面领先。"
                if score is not None
                else "可比数据不足，竞品缺口不评分。"
            ),
        )


def _dimension_score(competitor: Competitor, dimension: str, source_key: str) -> int | None:
    direct = competitor.dimensions.get(dimension)
    if direct is not None:
        return direct
    mappings = {
        "Evidence": competitor.evidence_count,
        "Authority": competitor.authority_score,
        "AI推荐率": competitor.recommendation_rate,
        "品牌认知": competitor.mention_rate,
    }
    return mappings.get(dimension, competitor.dimensions.get(source_key))
