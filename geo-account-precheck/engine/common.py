"""Small shared helpers for the diagnostic engine."""

from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from typing import Any

UNKNOWN = "UNKNOWN"
FACT = "FACT"
INFERENCE = "INFERENCE"

ALLOWED_STATUSES = {FACT, INFERENCE, UNKNOWN}
ALLOWED_SOURCE_TYPES = {
    "official",
    "government",
    "media",
    "third_party",
    "user_provided",
    "social",
    "unknown",
}
ALLOWED_RESEARCH_MODES = {"manual", "provided", "external", "offline"}

ABSOLUTE_PATTERNS = [
    r"国内第一",
    r"行业第一",
    r"全球第一",
    r"最好",
    r"最佳",
    r"唯一",
    r"100%\s*解决",
    r"百分百",
    r"绝对",
    r"全网最强",
]


def is_unknown(value: Any) -> bool:
    if value is None:
        return True
    text = str(value or "").strip()
    if not text:
        return True
    return text.upper() in {"UNKNOWN", "待补充", "暂无", "未知"}


def has_content(value: Any) -> bool:
    if isinstance(value, (list, tuple, set)):
        return any(has_content(item) for item in value)
    if isinstance(value, dict):
        return any(has_content(item) for item in value.values())
    return not is_unknown(value)


def stringify(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "、".join(stringify(item) for item in value if has_content(item))
    if isinstance(value, dict):
        nested = value.get("value", value.get("name", ""))
        return stringify(nested)
    return str(value or "").strip()


def listify(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "、" in text or "," in text or "，" in text:
            return [part.strip() for part in re.split(r"[、,，;；\n]", text) if part.strip()]
        return [text]
    if isinstance(value, (list, tuple)):
        return [stringify(item) for item in value if has_content(item)]
    if isinstance(value, dict):
        return [stringify(value)] if has_content(value) else []
    text = str(value or "").strip()
    return [text] if text else []


def clamp(value: float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(value))))


def mean(values: list[float | int | None]) -> float:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def average_int(values: list[float | int | None]) -> int:
    return clamp(mean(values))


def normalize_status(value: Any, fallback: str = UNKNOWN) -> str:
    status = str(value or "").strip().upper()
    return status if status in ALLOWED_STATUSES else fallback


def normalize_source_type(value: Any, fallback: str = "unknown") -> str:
    source_type = str(value or "").strip().lower().replace("-", "_")
    return source_type if source_type in ALLOWED_SOURCE_TYPES else fallback


def to_dict(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dict(item) for item in value]
    return value


def source_label(source_type: str) -> str:
    labels = {
        "official": "企业官方",
        "government": "政府/监管",
        "media": "媒体",
        "third_party": "第三方",
        "user_provided": "用户提供",
        "social": "社交平台",
        "unknown": "未知来源",
    }
    return labels.get(source_type, source_type)


def has_exaggeration(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in ABSOLUTE_PATTERNS)


def now_iso() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d")
