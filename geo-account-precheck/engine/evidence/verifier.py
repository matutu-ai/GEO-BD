"""Evidence verification and score calculation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..common import clamp, has_exaggeration, source_label
from ..models.evidence import EvidenceItem, EvidenceScore

THIRD_PARTY_TYPES = {"third_party", "media", "government"}
STRONG_SOURCE_TYPES = {"official", "government", "third_party", "media"}


class EvidenceVerifier:
    def verify(self, items: list[EvidenceItem]) -> EvidenceScore:
        if not items:
            return EvidenceScore(status="UNKNOWN", gaps=["没有任何 Evidence 记录；不能凭空评分。"])
        item_scores: list[int] = []
        has_source = 0
        has_date = 0
        third_party = 0
        verified = 0
        conflicts: list[str] = []
        exaggeration_claims: list[str] = []

        for item in items:
            result = self.verify_item(item)
            item_scores.append(result["score"])
            checks = result["checks"]
            has_source += int(checks["has_source"])
            has_date += int(checks["has_date"])
            third_party += int(checks["third_party"])
            verified += int(item.verified)
            if checks["has_conflict"]:
                conflicts.append(item.id)
                for referenced_id in item.conflicts_with:
                    if referenced_id not in conflicts:
                        conflicts.append(referenced_id)
            if checks["no_exaggeration"] is False:
                exaggeration_claims.append(item.id)

        source_ratio = has_source / len(items)
        date_ratio = has_date / len(items)
        third_party_ratio = third_party / len(items)
        verified_ratio = verified / len(items)
        conflict_ratio = len(conflicts) / len(items)
        exaggeration_ratio = len(exaggeration_claims) / len(items)

        score = clamp(
            100
            * (
                0.25 * source_ratio
                + 0.20 * third_party_ratio
                + 0.15 * date_ratio
                + 0.20 * verified_ratio
                + 0.10 * (1 - conflict_ratio)
                + 0.10 * (1 - exaggeration_ratio)
            )
        )
        gaps = []
        if source_ratio < 1:
            gaps.append("部分 Evidence 缺少来源")
        if date_ratio < 1:
            gaps.append("部分 Evidence 缺少日期")
        if third_party_ratio < 0.5:
            gaps.append("第三方/独立来源不足，存在自述为主风险")
        if verified_ratio < 1:
            gaps.append("部分 Evidence 尚未核验")
        if conflicts:
            gaps.append("存在相互冲突的 Evidence")
        if exaggeration_claims:
            gaps.append("存在夸张或绝对化表述")

        checks = {
            "all_have_source": has_source == len(items),
            "all_have_date": has_date == len(items),
            "has_third_party": third_party > 0,
            "all_verified": verified == len(items),
            "no_conflicts": not conflicts,
            "no_exaggeration": not exaggeration_claims,
        }
        return EvidenceScore(
            score=score,
            item_count=len(items),
            verified_count=verified,
            third_party_count=third_party,
            with_source_count=has_source,
            conflicts=conflicts,
            gaps=gaps,
            checks=checks,
            status="COMPUTED",
        )

    def verify_item(self, item: EvidenceItem) -> dict[str, Any]:
        has_source = bool(item.source.strip())
        source_type = item.source_type
        checks = {
            "has_source": has_source,
            "has_date": bool(item.date.strip()),
            "verifiable": source_type in STRONG_SOURCE_TYPES,
            "third_party": source_type in THIRD_PARTY_TYPES,
            "first_party": source_type in {"official", "user_provided"},
            "has_conflict": bool(item.conflicts_with),
            "not_stale": not _is_stale(item.date),
            "no_exaggeration": not has_exaggeration(item.claim),
            "no_absolute_claim": not has_exaggeration(item.claim),
        }
        sub_scores = [
            100 if has_source and source_type != "unknown" else 0,
            100 if source_type in {"third_party", "government"} else 70 if source_type in {"media", "official"} else 20,
            100 if item.date.strip() and not _is_stale(item.date) else 40 if item.date.strip() else 0,
            100 if item.verified else 30,
            100 if not checks["has_conflict"] else 0,
            100 if not has_exaggeration(item.claim) else 0,
        ]
        score = clamp(sum(sub_scores) / len(sub_scores))
        return {
            "item_id": item.id,
            "score": score,
            "checks": checks,
            "source_label": source_label(item.source_type),
        }


def _is_stale(date_text: str) -> bool:
    if not date_text:
        return False
    parsed = _parse_date(date_text)
    if parsed is None:
        return False
    today = date.today()
    try:
        age = (today - parsed.date()).days
    except (TypeError, ValueError):
        return False
    return age > 730


def _parse_date(date_text: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(str(date_text)[:10], fmt)
        except ValueError:
            continue
    return None
