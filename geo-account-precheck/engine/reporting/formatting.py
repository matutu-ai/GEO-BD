"""Small display helpers shared by the V3 report renderers."""

from __future__ import annotations

from typing import Any, Iterable

from ..common import is_unknown
from .status import STATUS_LABELS, UNKNOWN


def text(value: Any, fallback: str = UNKNOWN) -> str:
    raw = str(value or "").strip()
    return raw if raw and not is_unknown(raw) else fallback


def join(values: Iterable[Any], separator: str = "、") -> str:
    clean = [str(value).strip() for value in values if str(value or "").strip()]
    return separator.join(dict.fromkeys(clean))


def number_text(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return UNKNOWN
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value))
        return str(value)
    return text(value)


def metric_value(metric: dict[str, Any]) -> str:
    return number_text(metric.get("value"))


def status_text(status: Any) -> str:
    label = STATUS_LABELS.get(str(status))
    return f"{text(status, UNKNOWN)}（{label}）" if label else text(status, UNKNOWN)


def score_text(value: Any) -> str:
    return number_text(value)
