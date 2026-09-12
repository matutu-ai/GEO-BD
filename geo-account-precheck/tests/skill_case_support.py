"""Shared loader for GEO-BD Diagnostic Skill Golden Cases."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = Path(__file__).resolve().parent / "cases" / "case_001_tuoshi_ventilation"
sys.path.insert(0, str(ROOT))

from engine.pipeline import DiagnosticPipeline  # noqa: E402
from engine.reporting.diagnostic_skill import (  # noqa: E402
    build_diagnostic_skill_report,
    render_diagnostic_skill_report,
)


def load_case() -> dict[str, Any]:
    return json.loads((CASE_ROOT / "company.json").read_text(encoding="utf-8"))


def load_constraints() -> dict[str, Any]:
    return json.loads((CASE_ROOT / "fact_constraints.json").read_text(encoding="utf-8"))


def run_case() -> tuple[dict[str, Any], dict[str, Any]]:
    diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(load_case())
    return diagnostic, build_diagnostic_skill_report(diagnostic)


def render_case() -> str:
    return render_diagnostic_skill_report(run_case()[1])
