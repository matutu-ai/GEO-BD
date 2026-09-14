"""Acceptance tests for the diagnosis and prescription handoff."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agents.diagnosis_agent import render_diagnosis_summary
from agents.prescription_agent import render_geo_prescription
from engine.pipeline import DiagnosticPipeline
from engine.validation.schema_validator import validate_against_schema_file
from skill_case_support import CASE_ROOT, ROOT, load_case


DIAGNOSIS_SCHEMA = ROOT / "schemas" / "diagnosis_summary_schema.json"
PRESCRIPTION_SCHEMA = ROOT / "schemas" / "geo_prescription_schema.json"


class DiagnosisPrescriptionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(load_case())
        cls.diagnosis = cls.diagnostic["diagnosis_summary"]
        cls.prescription = cls.diagnostic["geo_prescription"]

    def test_diagnosis_is_compact_and_fact_bounded(self) -> None:
        self.assertEqual(validate_against_schema_file(self.diagnosis, DIAGNOSIS_SCHEMA), [])
        self.assertEqual(self.diagnosis["company_position"], "人防通风系统供应商")
        self.assertIn("AI可以识别企业存在", self.diagnosis["ai_cognition_status"])
        self.assertIn("AI认知建立阶段", self.diagnosis["current_stage"])
        self.assertIn("企业定位不够明确", self.diagnosis["core_problems"])
        self.assertNotIn("人防门厂家", render_diagnosis_summary(self.diagnosis))

    def test_prescription_has_only_module_level_actions(self) -> None:
        self.assertEqual(validate_against_schema_file(self.prescription, PRESCRIPTION_SCHEMA), [])
        self.assertEqual(
            [item["title"] for item in self.prescription["prescriptions"]],
            ["企业AI定位优化", "企业信息资产完善", "专业内容建设", "信任体系建设"],
        )
        markdown = render_geo_prescription(self.prescription)
        self.assertIn("进入 GEO 优化执行流程", markdown)
        self.assertNotIn("人防密闭阀厂家", markdown)
        self.assertNotIn("文章题目", markdown)
        self.assertNotIn("发布排期", markdown)

    def test_missing_observations_are_explicit(self) -> None:
        data = load_case()
        data["ai_observations"] = []
        diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(data)
        summary = diagnostic["diagnosis_summary"]
        self.assertIn("【需客户补充真实资料】", summary["ai_cognition_status"])
        self.assertIn("AI认知待测阶段", summary["current_stage"])

    def test_cli_exports_diagnosis_and_prescription(self) -> None:
        script = ROOT / "scripts" / "run_diagnostic.py"
        with tempfile.TemporaryDirectory() as tmp:
            diagnosis_md = Path(tmp) / "diagnosis.md"
            diagnosis_json = Path(tmp) / "diagnosis.json"
            prescription_md = Path(tmp) / "prescription.md"
            prescription_json = Path(tmp) / "prescription.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--input",
                    str(CASE_ROOT / "company.json"),
                    "--offline",
                    "--ai-diagnosis-summary",
                    str(diagnosis_md),
                    "--ai-diagnosis-summary-json",
                    str(diagnosis_json),
                    "--geo-prescription",
                    str(prescription_md),
                    "--geo-prescription-json",
                    str(prescription_json),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                validate_against_schema_file(json.loads(diagnosis_json.read_text(encoding="utf-8")), DIAGNOSIS_SCHEMA),
                [],
            )
            self.assertEqual(
                validate_against_schema_file(json.loads(prescription_json.read_text(encoding="utf-8")), PRESCRIPTION_SCHEMA),
                [],
            )
            self.assertIn("# AI诊断总结", diagnosis_md.read_text(encoding="utf-8"))
            self.assertIn("# GEO优化处方", prescription_md.read_text(encoding="utf-8"))

    def test_cli_all_includes_new_handoff_files(self) -> None:
        script = ROOT / "scripts" / "run_diagnostic.py"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "output"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--input",
                    str(CASE_ROOT / "company.json"),
                    "--offline",
                    "--report-level",
                    "all",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in (
                "ai_diagnosis_summary.md",
                "ai_diagnosis_summary.json",
                "geo_prescription.md",
                "geo_prescription.json",
                "final_report.md",
            ):
                self.assertTrue((output / filename).exists(), filename)
            final_report = (output / "final_report.md").read_text(encoding="utf-8")
            self.assertIn("# GEO-BD诊断与优化处方", final_report)
            self.assertIn("德州拓晟通风设备有限公司", final_report)
            self.assertIn("## AI诊断总结", final_report)
            self.assertIn("## GEO优化处方", final_report)
            self.assertNotIn("人防密闭阀厂家", final_report)
            self.assertLessEqual(len(final_report.splitlines()), 30)


if __name__ == "__main__":
    unittest.main()
