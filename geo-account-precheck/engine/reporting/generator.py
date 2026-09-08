"""Top-level V3 report generation: DiagnosticResult -> ReportModel -> markdown."""

from __future__ import annotations

from typing import Any

from .executive_renderer import render_executive
from .insight_engine import InsightEngine
from .models import ReportModel
from .operational_renderer import render_operational
from .technical_renderer import render_technical


REPORT_LEVELS = ("executive", "operational", "technical", "all")
REPORT_RENDERERS = {
    "executive": render_executive,
    "operational": render_operational,
    "technical": render_technical,
}


def build_report_model(
    diagnostic: dict[str, Any],
    engine: InsightEngine | None = None,
) -> ReportModel:
    """Build the shared ReportModel once for all V3 renderers."""
    if engine is None:
        engine = InsightEngine(diagnostic)
    return engine.build(diagnostic)


def generate_report(
    diagnostic: dict[str, Any],
    level: str = "executive",
    model: ReportModel | None = None,
) -> str:
    """Render one markdown report for a DiagnosticResult.

    ``level="all"`` is not a single markdown artifact; use
    :func:`generate_reports` when multiple files are needed.
    """
    if level not in REPORT_RENDERERS:
        raise ValueError(f"unsupported report level: {level}")
    model = model or build_report_model(diagnostic)
    if level == "technical":
        return render_technical(diagnostic)
    return REPORT_RENDERERS[level](model)


def generate_reports(
    diagnostic: dict[str, Any],
    level: str = "all",
) -> dict[str, str]:
    """Return ``{level: markdown}`` for executive/operational/technical."""
    if level not in {"all", *REPORT_RENDERERS}:
        raise ValueError(f"unsupported report level: {level}")
    levels = list(REPORT_RENDERERS) if level == "all" else [level]
    model = build_report_model(diagnostic)
    return {item: generate_report(diagnostic, item, model) for item in levels}


def render_legacy_report(diagnostic: dict[str, Any]) -> str:
    """Backward-compatible V2 wrapper used by --legacy-report."""
    from engine.reports.generator import render_markdown

    return render_markdown(diagnostic)
