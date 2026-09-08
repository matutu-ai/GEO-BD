"""L3 Technical Report keeps the full V2 traceability dump available."""

from __future__ import annotations

from typing import Any


def render_technical(diagnostic: dict[str, Any]) -> str:
    """Render every raw diagnostic block for GEO experts and agents."""
    from engine.reports.generator import render_markdown

    return render_markdown(diagnostic)
