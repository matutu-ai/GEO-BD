"""EEAT scorer: Experience, Expertise, Authoritativeness, Trustworthiness."""

from __future__ import annotations

from typing import Any

from ..common import UNKNOWN, clamp
from ..models.entity import EntityProfile
from ..models.evidence import EvidenceItem, EvidenceScore


class EeatScorer:
    def score(
        self,
        entity: EntityProfile,
        items: list[EvidenceItem],
        evidence: EvidenceScore,
        eeaap: dict[str, Any],
    ) -> dict[str, Any]:
        experience_score = eeaap.get("experience", 0)
        expertise_score = _expertise_score(entity, items)
        authority_count = (
            len(entity.get_values("certificates"))
            + len(entity.get_values("patents"))
            + len(entity.get_values("media"))
            + len(entity.get_values("experts"))
        )
        authoritativeness_score = clamp(min(100, authority_count * 25 + eeaap.get("authoritativeness", 0) * 0.4))
        trustworthiness_score = _trust_score(entity, items, evidence)
        values = [experience_score, expertise_score, authoritativeness_score, trustworthiness_score]
        overall = clamp(sum(values) / len(values))

        return {
            "experience": experience_score,
            "expertise": expertise_score,
            "authoritativeness": authoritativeness_score,
            "trustworthiness": trustworthiness_score,
            "overall": overall,
            "gaps": _gaps(entity, evidence, values),
            "basis": {
                "experience": "沿用 EEAAP Experience 评分，避免重复造分。",
                "expertise": f"创始人 {len(entity.get_values('founders'))} 位、专家 {len(entity.get_values('experts'))} 位、产品/技术资料 {len(entity.get_values('products'))} 项。",
                "authoritativeness": f"资质 {len(entity.get_values('certificates'))} 项、专利 {len(entity.get_values('patents'))} 项、媒体 {len(entity.get_values('media'))} 条。",
                "trustworthiness": f"已核验 {evidence.verified_count}/{evidence.item_count}，第三方来源 {evidence.third_party_count} 条。",
            },
            "difference_from_eeaap": (
                "EEAAP 检查内容是否足够让 AI 敢于推荐并引用；EEAT 检查企业在网络上的信任基础是否可被搜到。"
                "两者分开，避免把'资质齐全'误判为'推荐就绪'。"
            ),
            "status": "COMPUTED" if evidence.item_count else UNKNOWN,
        }


def _expertise_score(entity: EntityProfile, items: list[EvidenceItem]) -> int:
    founder_count = len(entity.get_values("founders"))
    expert_count = len(entity.get_values("experts"))
    product_count = len(entity.get_values("products"))
    technical_items = [item for item in items if any(keyword in item.claim for keyword in ("专利", "研发", "技术", "参数"))]
    return clamp(founder_count * 25 + expert_count * 20 + product_count * 10 + len(technical_items) * 15)


def _trust_score(entity: EntityProfile, items: list[EvidenceItem], evidence: EvidenceScore) -> int:
    verified_ratio = (evidence.verified_count / evidence.item_count) if evidence.item_count else 0
    third_party_ratio = (evidence.third_party_count / evidence.item_count) if evidence.item_count else 0
    has_nap = bool(entity.is_known("website") or entity.is_known("contacts"))
    no_conflict = not evidence.conflicts
    trust = clamp(
        100
        * (
            0.30 * verified_ratio
            + 0.30 * third_party_ratio
            + 0.20 * int(has_nap)
            + 0.10 * int(no_conflict)
            + 0.10 * int(not entity.is_known("negative_information"))
        )
    )
    return trust


def _gaps(entity: EntityProfile, evidence: EvidenceScore, values: list[int]) -> list[str]:
    gaps = []
    if values[0] < 60:
        gaps.append("Experience：真实项目证据不足")
    if values[1] < 60:
        gaps.append("Expertise：专家/研发/技术证据不足")
    if values[2] < 60:
        gaps.append("Authoritativeness：第三方信任基础不足")
    if values[3] < 60:
        gaps.append("Trustworthiness：核验率或来源独立性不足")
    return gaps
