"""InsightEngine tests for turning DiagnosticResult into a ReportModel."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import ROOT, load_fixture, run_diagnostic

from engine.reporting import InsightEngine, build_report_model
from engine.validation.schema_validator import validate_against_schema_file


def no_observation_payload() -> dict:
    return {
        "company": {
            "name": "只做实体诊断测试企业",
            "business": "冷库设备",
            "products": ["组合式冷库"],
            "services": ["冷库设计"],
        },
        "ai_observations": [],
        "competitors": [
            {
                "name": "竞品A",
                "status": "confirmed",
                "mention_rate": 90,
                "recommendation_rate": 80,
                "citation_rate": 50,
                "sources": ["用户上报"],
            }
        ],
        "evidence": [],
    }


class InsightEngineTest(unittest.TestCase):
    def test_full_sample_produces_stable_report_facts(self) -> None:
        model = build_report_model(run_diagnostic(load_fixture())).to_dict()
        self.assertEqual(model["health"]["score"], 83)
        self.assertEqual(model["health"]["status"], "COMPUTED")
        metrics = model["core_metrics"]
        self.assertEqual(metrics["ai_cognition"]["value"], 100)
        self.assertEqual(metrics["ai_recommendation"]["value"], 100)
        self.assertEqual(metrics["ai_citation"]["value"], 100)
        self.assertEqual(metrics["scenario_coverage"]["value"], 100)
        self.assertEqual(metrics["ai_trust"]["value"], 46)
        self.assertEqual(len(model["top_problems"]), 3)
        self.assertTrue(model["opportunities"])
        self.assertTrue(model["action_plan"])
        self.assertEqual(len(model["evidence_refs"]), 5)
        self.assertEqual(model["evidence_conflicts"]["status"], "CONFLICT")
        share_items = model["competitor_summary"]["share_of_voice"]["items"]
        self.assertEqual([item["name"] for item in share_items], ["示例冷库设备公司", "竞品A"])
        self.assertEqual([item["share"] for item in share_items], [50.0, 50.0])
        self.assertEqual(
            validate_against_schema_file(model, ROOT / "schemas" / "report.schema.json"),
            [],
        )

    def test_empty_input_stays_insufficient_and_unknown(self) -> None:
        model = build_report_model(run_diagnostic({})).to_dict()
        self.assertEqual(model["health"]["score"], None)
        self.assertEqual(model["health"]["status"], "INSUFFICIENT_DATA")
        self.assertEqual(model["top_problems"], [])
        self.assertEqual(model["opportunities"], [])
        self.assertEqual(model["action_plan"], [])
        self.assertEqual(model["evidence_refs"], [])
        for key in ("ai_cognition", "ai_recommendation", "ai_citation", "ai_trust", "scenario_coverage"):
            metric = model["core_metrics"][key]
            self.assertEqual(metric["status"], "UNKNOWN")
            self.assertIsNone(metric["value"])
        self.assertEqual(model["evidence_conflicts"]["status"], "UNKNOWN")
        self.assertEqual(model["competitor_summary"]["status"], "UNKNOWN")
        self.assertEqual(model["competitor_summary"]["share_of_voice"]["items"], [])

    def test_competitor_numbers_are_not_treated_as_ai_observations(self) -> None:
        diagnostic = run_diagnostic(no_observation_payload())
        model = build_report_model(diagnostic).to_dict()
        for key in ("ai_cognition", "ai_recommendation", "ai_citation"):
            metric = model["core_metrics"][key]
            self.assertEqual(metric["status"], "UNKNOWN")
            self.assertIsNone(metric["value"])
        summary = model["competitor_summary"]
        self.assertEqual(summary["status"], "UNKNOWN")
        self.assertEqual(summary["share_of_voice"]["status"], "UNKNOWN")
        self.assertEqual(summary["share_of_voice"]["items"], [])
        self.assertEqual(summary["gap_edges"], [])
        self.assertEqual(summary["gap_count"], 0)
        self.assertIn("没有真实 AI Observation 可比数据", summary["basis"])
        competitor = summary["competitors"][0]
        self.assertEqual(competitor["name"], "竞品A")
        self.assertEqual(competitor["status"], "confirmed")
        self.assertEqual(competitor["sources"], ["用户上报"])
        for key in ("mention_rate", "recommendation_rate", "citation_rate", "evidence_count", "authority_score"):
            self.assertIsNone(competitor[key])


if __name__ == "__main__":
    unittest.main()
