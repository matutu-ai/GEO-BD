"""Acceptance tests for the V3 AI growth diagnosis contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.pipeline import DiagnosticPipeline
from engine.reporting.growth_report import render_growth_report
from engine.validation.schema_validator import validate_against_schema_file
from skill_case_support import CASE_ROOT, ROOT, load_case


SCHEMAS = {
    "ai_visibility": ROOT / "schemas" / "ai_visibility.schema.json",
    "eeat_score": ROOT / "schemas" / "eeat_score.schema.json",
    "geo_gap": ROOT / "schemas" / "geo_gap.schema.json",
    "growth_score": ROOT / "schemas" / "growth_score.schema.json",
    "growth_prescription": ROOT / "schemas" / "prescription.schema.json",
}


class GrowthDiagnosisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(load_case())

    def test_all_new_outputs_match_schema(self) -> None:
        for key, schema in SCHEMAS.items():
            self.assertEqual(validate_against_schema_file(self.diagnostic[key], schema), [], key)

    def test_visibility_stage_uses_real_observations(self) -> None:
        result = self.diagnostic["ai_visibility"]
        self.assertEqual(result["brand_recognition"], 50)
        self.assertEqual(result["business_understanding"], 50)
        self.assertEqual(result["trust_level"], 17)
        self.assertEqual(result["recommend_probability"], 33)
        self.assertEqual(result["visibility_stage"], "KNOWN")

    def test_eeat_is_four_25_point_dimensions(self) -> None:
        result = self.diagnostic["eeat_score"]
        self.assertEqual(result["total"], 61)
        self.assertEqual(sum(result[key] for key in ("expertise", "experience", "authority", "trust")), 61)
        self.assertTrue(all(0 <= result[key] <= 25 for key in ("expertise", "experience", "authority", "trust")))

    def test_growth_score_uses_requested_weights(self) -> None:
        score = self.diagnostic["growth_score"]
        self.assertEqual(score["dimensions"], {"ai_visibility": 38, "positioning": 83, "eeat": 61, "content": 58})
        self.assertEqual(score["weights"], {"ai_visibility": 0.3, "positioning": 0.2, "eeat": 0.3, "content": 0.2})
        self.assertEqual(score["total"], 58)
        self.assertEqual(score["stage"], "AI识别阶段")

    def test_gap_map_and_prescription_are_module_level(self) -> None:
        gaps = self.diagnostic["geo_gap"]["gaps"]
        self.assertIn("企业定位与公开信息待校准", [item["problem"] for item in gaps])
        self.assertIn("用户需求场景不足", [item["problem"] for item in gaps])
        prescription = self.diagnostic["growth_prescription"]
        self.assertEqual(len(prescription["priority_actions"]), 4)
        self.assertIn("30_days", prescription)
        self.assertIn("90_days", prescription)
        self.assertNotIn("人防门厂家", json.dumps(prescription, ensure_ascii=False))
        self.assertNotIn("关键词", json.dumps(prescription, ensure_ascii=False))

    def test_missing_ai_observations_are_unknown(self) -> None:
        data = load_case()
        data["ai_observations"] = []
        diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(data)
        visibility = diagnostic["ai_visibility"]
        self.assertEqual(visibility["visibility_stage"], "UNKNOWN")
        self.assertIsNone(visibility["recommend_probability"])
        self.assertIn("【需企业提供真实佐证】", visibility["issues"])

    def test_growth_report_contains_required_sections(self) -> None:
        report = render_growth_report(self.diagnostic)
        for heading in (
            "# 企业AI增长诊断报告",
            "## 1 企业AI认知总览",
            "## 2 企业定位诊断",
            "## 3 AI可见度分析",
            "## 4 用户需求场景",
            "## 5 GEO竞争分析",
            "## 6 EEAT信任评分",
            "## 7 GEO缺口地图",
            "## 8 GEO增长处方",
        ):
            self.assertIn(heading, report)

    def test_main_entrypoint_generates_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "main.py"), "--output", tmp],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in (
                "GEO_AI诊断报告.md",
                "ai_visibility.json",
                "eeat_score.json",
                "geo_gap.json",
                "growth_prescription.json",
                "企业定位分析.md",
                "GEO缺口地图.md",
                "EEAT评分报告.md",
                "竞争分析.md",
                "GEO优化处方.md",
            ):
                self.assertTrue((Path(tmp) / filename).exists(), filename)

    def test_repository_main_entrypoint_generates_required_files(self) -> None:
        repository_root = ROOT.parent
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(repository_root / "main.py"), "--output", tmp],
                cwd=repository_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(tmp) / "GEO_AI诊断报告.md").exists())


if __name__ == "__main__":
    unittest.main()
