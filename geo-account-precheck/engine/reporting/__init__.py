"""V3 report architecture: DiagnosticResult -> InsightEngine -> ReportModel -> renderers."""

from .generator import (
    REPORT_LEVELS,
    build_report_model,
    generate_report,
    generate_reports,
    render_legacy_report,
)
from .insight_engine import InsightEngine
from .models import ReportModel
from .diagnostic_skill import build_diagnostic_skill_report, render_diagnostic_skill_report

__all__ = [
    "REPORT_LEVELS",
    "InsightEngine",
    "ReportModel",
    "build_report_model",
    "generate_report",
    "generate_reports",
    "render_legacy_report",
    "build_diagnostic_skill_report",
    "render_diagnostic_skill_report",
]
