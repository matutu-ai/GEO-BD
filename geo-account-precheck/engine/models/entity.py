"""Standard enterprise entity model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import is_unknown


@dataclass
class FactValue:
    value: str = ""
    status: str = "UNKNOWN"
    confidence: int = 0
    source: str = ""
    source_type: str = "unknown"
    verified: bool = False
    last_checked: str = ""

    @classmethod
    def unknown(cls) -> "FactValue":
        return cls(value="", status="UNKNOWN", confidence=0, source_type="unknown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "status": self.status,
            "confidence": self.confidence,
            "source": self.source,
            "source_type": self.source_type,
            "verified": self.verified,
            "last_checked": self.last_checked,
        }


@dataclass
class EntityProfile:
    research_mode: str = "provided"
    fields: dict[str, list[FactValue]] = field(default_factory=dict)
    raw_materials: list[Any] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def get_values(self, key: str) -> list[str]:
        values = [item.value for item in self.fields.get(key, []) if not is_unknown(item.value)]
        return [value for value in values if value]

    def get_value(self, key: str) -> str:
        values = self.get_values(key)
        return values[0] if values else ""

    def known_keys(self) -> list[str]:
        return [key for key, values in self.fields.items() if any(not is_unknown(v.value) for v in values)]

    def is_known(self, key: str) -> bool:
        return any(not is_unknown(item.value) for item in self.fields.get(key, []))

    def count_status(self, status: str) -> int:
        return sum(
            1
            for values in self.fields.values()
            for item in values
            if item.status == status and not is_unknown(item.value)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "research_mode": self.research_mode,
            "fields": {key: [item.to_dict() for item in values] for key, values in self.fields.items()},
            "raw_materials": self.raw_materials,
            "missing": self.missing,
        }
