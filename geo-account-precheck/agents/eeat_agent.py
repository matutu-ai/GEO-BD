"""Adapt the existing EEAT analysis into a 25-point category scorecard."""

from __future__ import annotations

from typing import Any


UNKNOWN = "【需企业提供真实佐证】"


class EEATTrustAgent:
    """Expose Expertise, Experience, Authority and Trust as four 25-point scores."""

    def build(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        eeat = diagnostic.get("eeat") or {}
        has_evidence = bool((diagnostic.get("evidence_graph") or {}).get("items"))
        computed = eeat.get("status") == "COMPUTED" and has_evidence
        if not computed:
            return {
                "expertise": None,
                "experience": None,
                "authority": None,
                "trust": None,
                "total": None,
                "missing_assets": [UNKNOWN],
            }

        values = {
            "expertise": _quarter(eeat.get("expertise")),
            "experience": _quarter(eeat.get("experience")),
            "authority": _quarter(eeat.get("authoritativeness")),
            "trust": _quarter(eeat.get("trustworthiness")),
        }
        missing = [str(item) for item in eeat.get("gaps") or []]
        if not missing:
            missing = ["当前诊断未记录单独的 EEAT 资产缺口；仍需核验来源。"]
        return {**values, "total": sum(values.values()), "missing_assets": missing}


def _quarter(value: Any) -> int:
    try:
        return max(0, min(25, round(float(value) / 4)))
    except (TypeError, ValueError):
        return 0
