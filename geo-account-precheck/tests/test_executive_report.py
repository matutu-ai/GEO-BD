"""Executive (L1) report renderer tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture, run_diagnostic

from engine.reporting import build_report_model, generate_report


def no_observation_payload() -> dict:
    return {
        "company": {
            "name": "只做实体诊断测试企业",
            "business": "冷库设备",
            "products": ["组合式冷库"],
            "services": ["冷库设计"],
        },
        "ai_observations": [],
        "competitors": [],
        "evidence": [],
    }


class ExecutiveReportTest(unittest.TestCase):
    def test_full_sample_report_contains_decision_first_sections(self) -> None:
        diagnostic = run_diagnostic(load_fixture())
        model = build_report_model(diagnostic)
        markdown = generate_report(diagnostic, "executive", model)
        self.assertIn("# GEO诊断报告", markdown)
        self.assertIn("83 / 100", markdown)
        self.assertIn("AI 已经能够做到", markdown)
        self.assertIn("## 当前最影响GEO的3个问题", markdown)
        self.assertIn("## 最值得抢的3个机会", markdown)
        self.assertIn("## 接下来怎么做", markdown)

    def test_empty_input_explains_what_is_missing(self) -> None:
        diagnostic = run_diagnostic({})
        model = build_report_model(diagnostic)
        markdown = generate_report(diagnostic, "executive", model)
        self.assertIn("# GEO诊断报告", markdown)
        self.assertIn("当前只能进行基础数据检查，无法进行完整 GEO", markdown)
        self.assertIn("真实 AI Observation", markdown)
        self.assertNotIn("83 / 100", markdown)

    def test_company_without_observation_does_not_claim_ai_performance(self) -> None:
        diagnostic = run_diagnostic(no_observation_payload())
        model = build_report_model(diagnostic)
        markdown = generate_report(diagnostic, "executive", model)
        self.assertIn("当前只能进行基础实体诊断，无法进行完整 AI 表现判断", markdown)
        self.assertIn("当前没有真实 AI Observation 数据", markdown)


if __name__ == "__main__":
    unittest.main()
