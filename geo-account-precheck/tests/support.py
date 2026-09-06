"""Shared test fixtures and helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.pipeline import DiagnosticPipeline  # noqa: E402
from engine.reports.generator import render_markdown  # noqa: E402
from engine.validation.schema_validator import validate_against_schema_file  # noqa: E402


def fixture_path(name: str = "sample_company.json") -> Path:
    return Path(__file__).resolve().parent / "fixtures" / name


def load_fixture(name: str = "sample_company.json") -> dict[str, Any]:
    return json.loads(fixture_path(name).read_text(encoding="utf-8"))


def run_diagnostic(data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = load_fixture() if data is None else data
    return DiagnosticPipeline(offline=True, research_mode="offline").run(payload)


def validate_diagnostic(result: dict[str, Any]) -> list[str]:
    return validate_against_schema_file(result, ROOT / "schemas" / "diagnostic.schema.json")


def render(result: dict[str, Any]) -> str:
    return render_markdown(result)
