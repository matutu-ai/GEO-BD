"""Strict GEO-BD Diagnostic Skill export for downstream AI learning.

This module intentionally delegates to the repository's V1 Skill adapter.
The exported JSON and Markdown therefore remain identical to the Skill
contract instead of introducing a parallel learning schema.
"""

from __future__ import annotations

from typing import Any

from .reporting.diagnostic_skill import (
    build_diagnostic_skill_report,
    render_diagnostic_skill_report,
)


def build_ai_learning_pack(diagnostic: dict[str, Any]) -> dict[str, Any]:
    """Export exactly the GEO-BD Diagnostic Skill V1 JSON contract."""

    return build_diagnostic_skill_report(diagnostic)


def render_ai_learning_pack(pack: dict[str, Any]) -> str:
    """Export exactly the GEO-BD Diagnostic Skill V1 Markdown template."""

    return render_diagnostic_skill_report(pack)
