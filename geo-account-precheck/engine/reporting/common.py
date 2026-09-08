"""Small shared readers used by the V3 insight and render layers."""

from __future__ import annotations

from typing import Any

from ..common import clamp, is_unknown, source_label


def real_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    """Return observations that are real observed/provided answers only."""
    cognition = diagnostic.get("ai_cognition") or {}
    result: list[dict[str, Any]] = []
    for item in cognition.get("observations") or []:
        status = str(item.get("status") or item.get("observation_mode") or "")
        if status in {"observed", "provided"} and str(item.get("query") or "").strip():
            result.append(item)
    return result


def all_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return list((diagnostic.get("ai_cognition") or {}).get("observations") or [])


def evidence_items(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return list((diagnostic.get("evidence_graph") or {}).get("items") or [])


def query_list(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return list((diagnostic.get("query_matrix") or {}).get("queries") or [])


def entity_value(entity: dict[str, Any], key: str) -> str:
    for item in (entity.get("fields") or {}).get(key) or []:
        value = str(item.get("value") or "").strip()
        if value and not is_unknown(value):
            return value
    return ""


def entity_values(entity: dict[str, Any], key: str) -> list[str]:
    values: list[str] = []
    for item in (entity.get("fields") or {}).get(key) or []:
        value = str(item.get("value") or "").strip()
        if value and not is_unknown(value) and value not in values:
            values.append(value)
    return values


def observation_ids(observations: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for observation in observations:
        query = str(observation.get("query") or "").strip()
        if query and query not in result:
            result.append(query)
    return result


def source_ids(observations: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for observation in observations:
        for source in observation.get("sources") or []:
            text = str(source or "").strip()
            if text and text not in result:
                result.append(text)
    return result


def rate_value(block: dict[str, Any], key: str) -> int | None:
    if block.get("status") not in {"COMPUTED", "OBSERVED"}:
        return None
    value = block.get(key)
    return None if value is None else clamp(value)


def source_type_label(source_type: Any) -> str:
    return source_label(str(source_type or "unknown"))
