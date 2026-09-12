"""Golden Case 001: full Diagnostic Skill V1 pipeline and report contract."""

from __future__ import annotations

import unittest
from pathlib import Path
import subprocess
import sys

from skill_case_support import ROOT, render_case, run_case
from engine.validation.schema_validator import validate_against_schema_file


SKILL_SCHEMA = ROOT.parent / "skills" / "geo-bd-diagnostic-skill" / "references" / "diagnostic-output.schema.json"


class FullPipelineGoldenTest(unittest.TestCase):
    def test_report_matches_v1_schema_and_has_nine_sections(self) -> None:
        diagnostic, report = run_case()
        self.assertEqual(diagnostic["meta"]["engine"], "GEO Diagnostic Engine")
        self.assertEqual(validate_against_schema_file(report, SKILL_SCHEMA), [])
        markdown = render_case()
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
            self.assertIn(heading, markdown)
        self.assertNotIn("人防门厂家", markdown.split("## 02 AI认知分析", 1)[0])

    def test_case_has_all_mock_materials(self) -> None:
        case_root = Path(__file__).resolve().parent / "cases" / "case_001_tuoshi_ventilation" / "input"
        expected = {"company_profile.md", "products.md", "qualification.md", "cases.md", "website_snapshot.md"}
        self.assertEqual({path.name for path in case_root.iterdir()}, expected)

    def test_v1_cli_runs_the_golden_case(self) -> None:
        script = ROOT / "scripts" / "run_geo_bd_diagnostic.py"
        case = Path(__file__).resolve().parent / "cases" / "case_001_tuoshi_ventilation" / "company.json"
        result = subprocess.run(
            [sys.executable, str(script), "--input", str(case), "--summary", "--offline"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GEO-BD Diagnostic Skill V1.0", result.stdout)
        self.assertIn("GEO Score: 58 COMPUTED", result.stdout)


if __name__ == "__main__":
    unittest.main()
