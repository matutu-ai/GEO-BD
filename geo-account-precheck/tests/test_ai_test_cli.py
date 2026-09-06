"""CLI tests for run_ai_test, compare_reports and the run_diagnosis alias."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIAGNOSIS = ROOT / "scripts" / "run_diagnosis.py"
RUN_AI_TEST = ROOT / "scripts" / "run_ai_test.py"
COMPARE_REPORTS = ROOT / "scripts" / "compare_reports.py"
SAMPLE = ROOT / "tests" / "fixtures" / "sample_company.json"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class AiTestCliTest(unittest.TestCase):
    def test_ai_test_records_produce_rates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tests_path = Path(tmp) / "ai-test.json"
            output_path = Path(tmp) / "ai-test-result.json"
            tests_path.write_text(
                json.dumps(
                    [
                        {
                            "query": "冷库工程有哪些值得推荐的公司",
                            "company_mentioned": True,
                            "company_recommended": True,
                            "citation_found": True,
                            "position": 2,
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = _run(RUN_AI_TEST, "--tests", str(tests_path), "--output", str(output_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "COMPUTED")
            self.assertEqual(data["mention_rate"], 100)
            self.assertEqual(data["recommendation_rate"], 100)
            self.assertEqual(data["citation_rate"], 100)
            self.assertEqual(data["average_position"], 2.0)

    def test_empty_ai_test_stays_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tests_path = Path(tmp) / "ai-test.json"
            tests_path.write_text("[]", encoding="utf-8")
            result = _run(RUN_AI_TEST, "--tests", str(tests_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "NOT_RUN")
            self.assertTrue(data["insufficient_data"])
            self.assertIsNone(data["mention_rate"])
            self.assertEqual(data["input_records"], 0)


class CompareReportsCliTest(unittest.TestCase):
    def _sample_report(self) -> dict:
        sys.path.insert(0, str(ROOT))
        from support import run_diagnostic

        return run_diagnostic(json.loads(SAMPLE.read_text(encoding="utf-8")))

    def test_before_after_comparison_writes_markdown(self) -> None:
        before = self._sample_report()
        after = copy.deepcopy(before)
        after["scores"]["geo_score"] = (before["scores"]["geo_score"] or 0) + 5
        after["evidence_graph"]["items"].append(copy.deepcopy(after["evidence_graph"]["items"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            before_path = Path(tmp) / "before.json"
            after_path = Path(tmp) / "after.json"
            output_path = Path(tmp) / "comparison.md"
            before_path.write_text(json.dumps(before, ensure_ascii=False), encoding="utf-8")
            after_path.write_text(json.dumps(after, ensure_ascii=False), encoding="utf-8")
            result = _run(
                COMPARE_REPORTS,
                "--before",
                str(before_path),
                "--after",
                str(after_path),
                "--output",
                str(output_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            markdown = output_path.read_text(encoding="utf-8")
            self.assertIn("# GEO Before / After Comparison", markdown)
            self.assertIn("GEO Score", markdown)


class RunDiagnosisAliasTest(unittest.TestCase):
    def test_alias_writes_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "diagnosis.json"
            result = _run(RUN_DIAGNOSIS, "--input", str(SAMPLE), "--json", str(output_path), "--offline")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("scenarios", data)
            self.assertIn("ai_tests", data)


if __name__ == "__main__":
    unittest.main()
