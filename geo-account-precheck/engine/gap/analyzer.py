"""GEO gap analyzer."""

from __future__ import annotations

from typing import Any

from ..common import UNKNOWN, clamp
from ..models.entity import EntityProfile
from ..models.evidence import EvidenceScore
from ..models.gap import GeoGap
from ..models.query import QueryCoverage
from ..query.matrix import QueryMatrix
from ..scorecard import entity_score


def analyze_gaps(
    entity: EntityProfile,
    evidence: EvidenceScore,
    eeaap: dict[str, Any],
    eeat: dict[str, Any],
    coverage: QueryCoverage,
    query_matrix: QueryMatrix,
    competitor_status: str,
    competitor_score: int | None,
    issues: list[str],
) -> dict[str, Any]:
    entity_health = entity_score(entity)
    entity_flags = ["no_basics"] if not entity.is_known("name") or not entity.is_known("business") else []

    if query_matrix.queries:
        query_health = coverage.score if coverage.status != UNKNOWN and coverage.score is not None else None
        query_flags = [] if query_health is not None else ["no_observations"]
    else:
        query_health = None
        query_flags = ["no_queries"]

    if evidence.item_count:
        evidence_health = evidence.score
        evidence_flags = []
    else:
        evidence_health = None
        evidence_flags = ["no_evidence"]

    citation_health = coverage.citation_rate
    if citation_health is None:
        citation_health = None

    nap_missing = not (entity.is_known("website") or entity.is_known("contacts"))
    nap_keywords = ("电话", "官网", "NAP", "露出")
    has_nap_issue = any(any(keyword in issue for keyword in nap_keywords) for issue in issues)
    if has_nap_issue and nap_missing:
        nap_health = 0
        nap_flags = ["nap_conflict"]
    elif nap_missing:
        nap_health = 30
        nap_flags = []
    else:
        nap_health = 100
        nap_flags = []

    content_health = _content_health(entity, query_matrix)
    gaps = [
        GeoGap.make(
            "Entity Gap",
            entity_health,
            f"企业实体已知度 {entity_health}/100；缺失：{', '.join(entity.missing) if entity.missing else '无'}。",
            critical_flags=entity_flags,
            recommended_action="补齐企业基础字段后再进入评分。",
        ),
        GeoGap.make(
            "Query Gap",
            query_health,
            (
                "没有可诊断的 Query Matrix。"
                if not query_matrix.queries
                else "真实 AI 观察不足，无法可靠计算 Query Coverage。"
                if query_health is None
                else f"Query Coverage {query_health}/100，企业仍在部分真实问题中缺席。"
            ),
            critical_flags=query_flags,
            affected_queries=[item.query for item in query_matrix.queries[:5]],
            recommended_action="补充真实 AI 搜索观察并按高频问题补齐内容。",
        ),
        GeoGap.make(
            "Evidence Gap",
            evidence_health,
            f"Evidence Score {evidence.score}/100；{len(evidence.gaps)} 个核验缺口。" if evidence.item_count else "没有任何 Evidence 记录。",
            critical_flags=evidence_flags,
            recommended_action="建立可核验证据包并逐条标注来源、日期和第三方验证。",
        ),
        GeoGap.make(
            "Experience Gap",
            eeaap.get("experience"),
            str(eeaap.get("basis", {}).get("experience", "缺少经验证据。")),
            recommended_action="补充真实客户案例、项目过程和结果。",
        ),
        GeoGap.make(
            "Authority Gap",
            eeat.get("authoritativeness"),
            str(eeat.get("basis", {}).get("authoritativeness", "缺少权威背书。")),
            recommended_action="补充第三方权威证明、专家和行业背书。",
        ),
        GeoGap.make(
            "Content Gap",
            content_health,
            "企业产品/服务实体与 Query 场景覆盖不足。",
            critical_flags=["no_queries"] if not query_matrix.queries else [],
            recommended_action="按高频 Query 补齐有证据的画像内容。",
        ),
        GeoGap.make(
            "Citation Gap",
            citation_health,
            (
                "没有 AI 引用观察数据。"
                if citation_health is None
                else f"AI 引用率 {citation_health}%；未被引用意味着内容没有被采信。"
            ),
            critical_flags=["no_observations"] if citation_health is None else [],
            recommended_action="复测时记录 AI 是否直接引用企业来源。",
        ),
        GeoGap.make(
            "Trust Gap",
            eeat.get("trustworthiness"),
            str(eeat.get("basis", {}).get("trustworthiness", "缺少信任基础。")),
            recommended_action="核验来源、统一 NAP 并清除冲突证据。",
        ),
        GeoGap.make(
            "Local/NAP Gap",
            nap_health,
            "全平台 NAP/官网/电话一致性数据缺失或存在冲突。",
            critical_flags=nap_flags,
            recommended_action="逐平台核验并统一 NAP、官网和电话信息。",
        ),
    ]
    if competitor_status == UNKNOWN:
        gaps.append(
            GeoGap.make(
                "Competitor Gap",
                None,
                "没有可靠竞品数据；不自动编造竞品。",
                critical_flags=["no_competitors"],
                recommended_action="补充确认的竞品清单及可比观察。",
            )
        )
    else:
        gaps.append(
            GeoGap.make(
                "Competitor Gap",
                competitor_score,
                f"竞品可比缺口分数 {competitor_score}/100。",
                recommended_action="优先消除客户缺席但竞品被推荐的 Query。",
            )
        )

    serialized = [gap.to_dict() for gap in gaps]
    return {"gaps": serialized, "status": "COMPUTED", "count": len(serialized)}


def _content_health(entity: EntityProfile, query_matrix: QueryMatrix) -> int | None:
    entity_items = len(entity.get_values("products")) + len(entity.get_values("services"))
    if not entity_items and not query_matrix.queries:
        return None
    query_factor = min(100, len(query_matrix.queries) * 10)
    return clamp(min(100, entity_items * 25) * 0.6 + query_factor * 0.4)
