"""Tests for the compact downstream AI learning context."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.learning_pack import build_ai_learning_pack, render_ai_learning_pack
from engine.pipeline import DiagnosticPipeline
from engine.reporting.diagnostic_skill import build_diagnostic_skill_report
from engine.validation.schema_validator import validate_against_schema_file
from skill_case_support import CASE_ROOT, ROOT, load_case


PACK_SCHEMA = ROOT.parent / "skills" / "geo-bd-diagnostic-skill" / "references" / "diagnostic-output.schema.json"


class LearningPackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(load_case())
        cls.pack = build_ai_learning_pack(cls.diagnostic)
        cls.markdown = render_ai_learning_pack(cls.pack)

    def test_pack_matches_schema_and_is_bounded(self) -> None:
        expected = build_diagnostic_skill_report(self.diagnostic)
        self.assertEqual(self.pack, expected)
        self.assertEqual(validate_against_schema_file(self.pack, PACK_SCHEMA), [])
        self.assertLessEqual(len(self.markdown), 12000)
        self.assertIn("德州拓晟通风设备有限公司", self.markdown)
        self.assertIn("GEO-BD Diagnostic Skill V1.0", self.markdown)

    def test_pack_uses_skill_sections_and_preserves_positioning_boundary(self) -> None:
        self.assertEqual(self.pack["company_status"]["position"], "人防通风系统供应商")
        self.assertNotIn("人防门厂家", self.markdown.split("## 02 AI认知分析", 1)[0])
        for heading in (
            "## 01 企业当前状态",
            "## 02 AI认知分析",
            "## 03 Query覆盖分析",
            "## 04 Evidence可信度",
            "## 05 竞品差距",
            "## 06 GEO Score",
            "## 07 GEO缺口",
            "## 08 P0-P3优化建议",
            "## 09 下一阶段执行路线",
        ):
            self.assertIn(heading, self.markdown)

    def test_pack_marks_missing_observations_without_inventing_metrics(self) -> None:
        data = load_case()
        data["ai_observations"] = []
        diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(data)
        pack = build_ai_learning_pack(diagnostic)
        self.assertEqual(pack["ai_cognition"]["status"], "UNKNOWN")
        self.assertIsNone(pack["ai_cognition"]["brand_recognition"])
        self.assertIn("没有真实 AI 观察结果", pack["ai_cognition"]["basis"])

    def test_cli_all_writes_learning_pack_files(self) -> None:
        script = ROOT / "scripts" / "run_diagnostic.py"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "output"
            result = subprocess.run(
                [sys.executable, str(script), "--input", str(CASE_ROOT / "company.json"), "--offline", "--report-level", "all", "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            markdown = output / "ai_learning_pack.md"
            structured = output / "ai_learning_pack.json"
            self.assertTrue(markdown.exists())
            self.assertTrue(structured.exists())
            payload = json.loads(structured.read_text(encoding="utf-8"))
            self.assertEqual(validate_against_schema_file(payload, PACK_SCHEMA), [])
            self.assertIn("# GEO诊断报告", markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
