"""EEAAP scorer: Experience, Evidence, Authoritativeness, Accuracy, Perspective."""

from __future__ import annotations

from typing import Any

from ..common import INFERENCE, UNKNOWN, clamp, has_exaggeration
from ..models.entity import EntityProfile
from ..models.evidence import EvidenceItem


class EeaapScorer:
    def score(
        self,
        entity: EntityProfile,
        items: list[EvidenceItem],
        evidence_score: int | None,
    ) -> dict[str, Any]:
        by_category = _categorize(items)
        experience_score = _category_score(
            by_category["experience"],
            extra=len(entity.get_values("customers")) + len(entity.get_values("locations")),
            cap_bonus=25,
        )
        evidence_score_value = evidence_score if evidence_score is not None else 0
        evidence_items = [*by_category["evidence"], *by_category["experience"]]
        evidence_independent = [item for item in evidence_items if item.source_type in {"third_party", "media", "government"}]
        evidence_dimension = clamp(
            0.6 * evidence_score_value
            + 0.4 * min(100, len(evidence_independent) * 30 + len(evidence_items) * 10)
        )

        authority_count = (
            len(entity.get_values("certificates"))
            + len(entity.get_values("patents"))
            + len(entity.get_values("experts"))
            + len(entity.get_values("media"))
        )
        authority_items = by_category["authoritativeness"]
        authority_dimension = _category_score(
            authority_items,
            extra=authority_count,
            cap_bonus=20,
            base_per_item=30,
        )

        accuracy_claims = [item for item in items if item.claim]
        if accuracy_claims:
            clean_ratio = sum(1 for item in accuracy_claims if not has_exaggeration(item.claim)) / len(accuracy_claims)
            accuracy_dimension = clamp(clean_ratio * 100)
        else:
            accuracy_dimension = 0
        perspective_dimension = _category_score(
            by_category["perspective"],
            extra=0,
            base_per_item=50,
            cap_bonus=50,
        )

        values = [experience_score, evidence_dimension, authority_dimension, accuracy_dimension, perspective_dimension]
        overall = clamp(sum(values) / len(values))
        gaps: list[str] = []
        if experience_score < 60:
            gaps.append("Experience：缺少真实落地项目/客户场景证据")
        if evidence_dimension < 60:
            gaps.append("Evidence：第三方可核验证据不足")
        if authority_dimension < 60:
            gaps.append("Authoritativeness：资质/专家/第三方背书不足")
        if accuracy_dimension < 100 and accuracy_claims:
            gaps.append("Accuracy：存在需人工复核的表述")
        if perspective_dimension < 60:
            gaps.append("Perspective：缺少适用边界与局限说明")

        return {
            "experience": experience_score,
            "evidence": evidence_dimension,
            "authoritativeness": authority_dimension,
            "accuracy": accuracy_dimension,
            "perspective": perspective_dimension,
            "overall": overall,
            "gaps": gaps,
            "basis": {
                "experience": _basis(experience_score, by_category["experience"], "真实案例、项目经验、场景深度"),
                "evidence": _basis(evidence_dimension, evidence_items, "参数、案例、实拍、检测、第三方验证"),
                "authoritativeness": _basis(authority_dimension, [*authority_items, *entity.get_values("certificates")], "资质、专家、第三方媒体、行业地位"),
                "accuracy": f"{len(accuracy_claims)} 条声明参与绝对化/夸张表述检查" if accuracy_claims else "无声明可检查，评分按 0 处理",
                "perspective": _basis(perspective_dimension, by_category["perspective"], "场景边界、适用条件、局限"),
            },
            "status": "COMPUTED" if overall > 0 or items else UNKNOWN,
        }


def _categorize(items: list[EvidenceItem]) -> dict[str, list[EvidenceItem]]:
    result = {"experience": [], "evidence": [], "authoritativeness": [], "accuracy": [], "perspective": []}
    category_keywords = {
        "experience": ("experience", "经验", "案例", "case", "project"),
        "evidence": ("evidence", "证据", "参数", "实拍", "检测", "验证"),
        "authoritativeness": ("authoritativeness", "权威", "资质", "证书", "专利", "媒体"),
        "accuracy": ("accuracy", "准确", "无夸大"),
        "perspective": ("perspective", "视角", "局限", "不适用", "适用场景"),
    }
    for item in items:
        text = f"{item.category} {item.claim}".lower()
        assigned = False
        for key, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                result[key].append(item)
                assigned = True
        if not assigned:
            result["evidence"].append(item)
    return result


def _category_score(
    items: list[Any],
    extra: int = 0,
    base_per_item: int = 25,
    cap_bonus: int = 20,
) -> int:
    count = len(items)
    score = count * base_per_item + extra * cap_bonus
    return clamp(score)


def _basis(score: int, items: list[Any], label: str) -> str:
    ids = [getattr(item, "id", str(item)) for item in items if hasattr(item, "id")]
    return f"{label}；得分 {score}/100；证据：{', '.join(ids) if ids else '暂无'}"
