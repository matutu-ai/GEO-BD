"""Render one interaction prompt without changing diagnostic business logic."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


UNKNOWN = "【需企业补充真实资料】"
PROMPT_ROOT = Path(__file__).resolve().parent
STAGES = {
    "welcome": "welcome.md",
    "intake": "intake.md",
    "diagnosis": "diagnosis.md",
    "competition": "competition.md",
    "visibility": "visibility.md",
    "personas": "personas.md",
    "prescription": "prescription.md",
    "report": "report.md",
}
PLACEHOLDER = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def available_stages() -> tuple[str, ...]:
    """Return stage ids in the order shown to a user."""

    return tuple(STAGES)


def render_prompt(stage: str, context: dict[str, Any] | None = None) -> str:
    """Render one prompt; missing dynamic values stay explicitly unknown."""

    try:
        filename = STAGES[stage]
    except KeyError as exc:
        raise ValueError(f"Unknown interaction stage: {stage}") from exc
    template = (PROMPT_ROOT / filename).read_text(encoding="utf-8")
    values = {key: _format_value(value) for key, value in (context or {}).items()}
    return PLACEHOLDER.sub(lambda match: values.get(match.group(1), UNKNOWN), template)


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return UNKNOWN
    if isinstance(value, (list, tuple, set)):
        return "、".join(str(item) for item in value) or UNKNOWN
    return str(value)
