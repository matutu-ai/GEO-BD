"""ReportModel problem ranking tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture, run_diagnostic

from engine.reporting import build_report_model


def entity_only_payload() -> dict:
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


class ProblemEngineTest(unittest.TestCase):
    def test_full_sample_top_problems_are_traceable_and_limited_to_three(self) -> None:
        model = build_report_model(run_diagnostic(load_fixture())).to_dict()
        problems = model["top_problems"]
        self.assertTrue(problems)
        self.assertLessEqual(len(problems), 3)
        self.assertEqual(len({problem["id"] for problem in problems}), len(problems))
        for problem in problems:
            self.assertRegex(problem["id"], r"^P\d{3}$")
            self.assertRegex(problem["priority"], r"^P[0-3]$")
            self.assertTrue(problem["title"])
            self.assertTrue(problem["affected_metrics"])
            self.assertTrue(problem["evidence_ids"])
            self.assertTrue(problem["source_gap_type"])

    def test_empty_input_has_no_problems(self) -> None:
        model = build_report_model(run_diagnostic({})).to_dict()
        self.assertEqual(model["top_problems"], [])

    def test_entity_only_input_keeps_entity_gaps(self) -> None:
        model = build_report_model(run_diagnostic(entity_only_payload())).to_dict()
        self.assertTrue(model["top_problems"])
        for problem in model["top_problems"]:
            self.assertEqual(problem["observation_ids"], [])
            self.assertEqual(problem["evidence_ids"], [])


if __name__ == "__main__":
    unittest.main()
