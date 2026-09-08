"""ReportModel action plan tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture, run_diagnostic

from engine.reporting import build_report_model


class ActionEngineTest(unittest.TestCase):
    def test_full_sample_actions_are_actionable_and_traceable(self) -> None:
        model = build_report_model(run_diagnostic(load_fixture())).to_dict()
        actions = model["action_plan"]
        self.assertTrue(actions)
        self.assertEqual(len({action["id"] for action in actions}), len(actions))
        for action in actions:
            self.assertRegex(action["id"], r"^A\d{3}$")
            self.assertRegex(action["priority"], r"^P[0-3]$")
            self.assertTrue(action["title"])
            self.assertTrue(action["tasks"])
            self.assertTrue(action["expected_impact"])
            self.assertEqual(len(action["source_problem_ids"]), 1)

    def test_entity_only_actions_do_not_claim_observation_support(self) -> None:
        payload = {
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
        model = build_report_model(run_diagnostic(payload)).to_dict()
        self.assertTrue(model["action_plan"])
        for action in model["action_plan"]:
            self.assertEqual(action["observation_ids"], [])

    def test_empty_input_has_no_actions(self) -> None:
        model = build_report_model(run_diagnostic({})).to_dict()
        self.assertEqual(model["action_plan"], [])


if __name__ == "__main__":
    unittest.main()
