"""CLI acceptance tests for the V2 diagnostic entry points."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIAGNOSTIC = ROOT / "scripts" / "run_diagnostic.py"
VALIDATE_DIAGNOSTIC = ROOT / "scripts" / "validate_diagnostic.py"
SAMPLE = ROOT / "tests" / "fixtures" / "sample_company.json"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class RunDiagnosticCliTest(unittest.TestCase):
    def test_template_prints_valid_input_json(self) -> None:
        result = _run(RUN_DIAGNOSTIC, "--template")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        for key in ("company", "materials", "ai_observations", "competitors", "evidence", "issues", "keyword_directions"):
            self.assertIn(key, data)

    def test_sample_run_writes_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "diagnostic.md"
            json_path = Path(tmp) / "diagnostic.json"
            result = _run(
                RUN_DIAGNOSTIC,
                "--input",
                str(SAMPLE),
                "--output",
                str(md_path),
                "--json",
                str(json_path),
                "--offline",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("GEO Score:", result.stdout)
            self.assertIn("Top P", result.stdout)
            self.assertIn("Evidence:", result.stdout)
            self.assertIn("AI Test:", result.stdout)
            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())
            self.assertIn("# GEO Diagnostic Report", md_path.read_text(encoding="utf-8"))
            report = json.loads(json_path.read_text(encoding="utf-8"))
            for key in ("meta", "entity", "ai_cognition", "query_matrix", "competitors", "evidence_graph", "scores"):
                self.assertIn(key, report)
            validation = _run(VALIDATE_DIAGNOSTIC, "--input", str(json_path))
            self.assertEqual(validation.returncode, 0, validation.stderr)
            self.assertIn("VALIDATION_OK", validation.stdout)

    def test_summary_only_prints_console_summary(self) -> None:
        result = _run(RUN_DIAGNOSTIC, "--input", str(SAMPLE), "--summary", "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GEO Score:", result.stdout)
        self.assertIn("Top P", result.stdout)
        self.assertNotIn("# GEO Diagnostic Report", result.stdout)

    def test_needs_input_writes_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            needs_path = Path(tmp) / "needs-input.md"
            result = _run(RUN_DIAGNOSTIC, "--input", str(SAMPLE), "--needs-input", str(needs_path), "--offline")
            self.assertEqual(result.returncode, 0, result.stderr)
            checklist = needs_path.read_text(encoding="utf-8")
            self.assertIn("# 需要补充的资料", checklist)
            self.assertIn("- 企业字段：", checklist)

    def test_markdown_flag_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "by-markdown-flag.md"
            result = _run(RUN_DIAGNOSTIC, "--input", str(SAMPLE), "--markdown", str(md_path), "--offline")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("GEO Score:", result.stdout)
            self.assertIn("## 19 Unknown / Missing Data", md_path.read_text(encoding="utf-8"))

    def test_missing_input_returns_usage_error(self) -> None:
        result = _run(RUN_DIAGNOSTIC)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--input is required", result.stderr)

    def test_check_returns_nonzero_for_empty_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "empty.json"
            input_path.write_text("{}", encoding="utf-8")
            result = _run(RUN_DIAGNOSTIC, "--input", str(input_path), "--check")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DIAGNOSTIC_INSUFFICIENT_DATA", result.stderr)
            self.assertIn("Data Quality", result.stderr)

    def test_check_passes_for_complete_sample(self) -> None:
        result = _run(RUN_DIAGNOSTIC, "--input", str(SAMPLE), "--check", "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_validate_detects_invalid_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "bad.json"
            report_path.write_text('{"not": "enough"}', encoding="utf-8")
            result = _run(VALIDATE_DIAGNOSTIC, "--input", str(report_path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("VALIDATION_ERROR", result.stderr)


if __name__ == "__main__":
    unittest.main()
