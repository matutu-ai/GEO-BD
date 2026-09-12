"""Acceptance tests for the operations-focused final GEO summary."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from skill_case_support import CASE_ROOT, ROOT, load_case
from engine.pipeline import DiagnosticPipeline
from engine.validation.schema_validator import validate_against_schema_file
from agents.final_summary_agent import render_final_summary


SUMMARY_SCHEMA = ROOT / "schemas" / "final_summary_schema.json"


class FinalSummaryAgentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(load_case())
        cls.summary = cls.diagnostic["final_summary"]
        cls.markdown = render_final_summary(cls.summary)

    def test_summary_matches_schema_and_uses_existing_diagnosis(self) -> None:
        self.assertEqual(validate_against_schema_file(self.summary, SUMMARY_SCHEMA), [])
        self.assertEqual(self.summary["company_name"], "德州拓晟通风设备有限公司")
        self.assertEqual(self.summary["entity_score"], 83)
        self.assertIn("人防通风系统供应商", self.summary["company_position"])
        self.assertIn("AI", self.summary["ai_cognition_summary"])
        self.assertIn("Query", self.summary["core_problem"])
        self.assertEqual(set(self.summary["optimization_priority"]), {"P0", "P1", "P2"})

    def test_summary_has_the_nine_operations_sections(self) -> None:
        for heading in (
            "## 1. 企业当前AI认知判断",
            "## 2. 当前优势",
            "## 3. 当前不足",
            "## 4. 企业实体完整度",
            "## 5. GEO关键词状态",
            "## 6. 用户搜索意图判断",
            "## 7. GEO核心问题总结",
            "## 8. GEO运营优化优先级",
            "## 9. 最终运营建议",
        ):
            self.assertIn(heading, self.markdown)

    def test_summary_does_not_turn_restricted_claims_into_positioning(self) -> None:
        self.assertNotIn("人防门厂家", self.summary["company_position"])
        self.assertNotIn("人防门厂家", self.markdown)
        self.assertNotIn("国家人防门定点企业", self.markdown)
        self.assertNotIn("虚构", self.markdown)
        self.assertNotIn("排名第一", self.markdown)

    def test_unknown_ai_observation_is_marked(self) -> None:
        data = load_case()
        data["ai_observations"] = []
        diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(data)
        summary = diagnostic["final_summary"]
        self.assertIn("【需客户补充真实资料】", summary["ai_cognition_summary"])
        self.assertIn("【需客户补充真实资料】", summary["keyword_status"]["covered"])

    def test_cli_all_writes_geo_summary(self) -> None:
        script = ROOT / "scripts" / "run_diagnostic.py"
        case = CASE_ROOT / "company.json"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "output"
            result = subprocess.run(
                [sys.executable, str(script), "--input", str(case), "--offline", "--report-level", "all", "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary_path = output / "geo_summary.md"
            self.assertTrue(summary_path.exists())
            self.assertIn("# GEO客户当前情况总结", summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
