"""V3 unknown handling tests for missing or non-observed data."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import run_diagnostic

from engine.reporting import InsightEngine, build_report_model


class UnknownHandlingTest(unittest.TestCase):
    def test_empty_input_is_never_presented_as_zero_performance(self) -> None:
        diagnostic = run_diagnostic({})
        model = build_report_model(diagnostic).to_dict()
        self.assertEqual(model["health"]["status"], "INSUFFICIENT_DATA")
        self.assertIsNone(model["health"]["score"])
        for key in ("ai_cognition", "ai_recommendation", "ai_citation", "ai_trust", "scenario_coverage"):
            self.assertEqual(model["core_metrics"][key]["status"], "UNKNOWN")
            self.assertIsNone(model["core_metrics"][key]["value"])
        self.assertEqual(model["competitor_summary"]["share_of_voice"]["items"], [])
        self.assertEqual(model["evidence_refs"], [])

    def test_reported_competitor_metrics_are_not_real_ai_observations(self) -> None:
        diagnostic = {
            "company": {"name": "只做实体诊断测试企业"},
            "ai_cognition": {"status": "UNKNOWN", "observations": []},
            "competitors": {
                "status": "PROVIDED",
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
            },
            "evidence_graph": {"items": []},
        }
        model = InsightEngine(diagnostic).build().to_dict()
        summary = model["competitor_summary"]
        self.assertEqual(summary["status"], "UNKNOWN")
        self.assertEqual(summary["gap_count"], 0)
        self.assertEqual(summary["share_of_voice"]["status"], "UNKNOWN")
        self.assertIsNone(summary["competitors"][0]["mention_rate"])
        self.assertIsNone(summary["competitors"][0]["citation_rate"])
        self.assertEqual(summary["basis"], "有确认竞品清单，但没有真实 AI Observation 可比数据，竞品 AI 指标不评分。")

    def test_no_observation_leaves_core_ai_rates_unknown(self) -> None:
        diagnostic = run_diagnostic(
            {
                "company": {"name": "只做实体诊断测试企业", "business": "冷库设备"},
                "ai_observations": [],
                "competitors": [],
                "evidence": [],
            }
        )
        model = build_report_model(diagnostic).to_dict()
        for key in ("ai_cognition", "ai_recommendation", "ai_citation"):
            self.assertEqual(model["core_metrics"][key]["status"], "UNKNOWN")
            self.assertIsNone(model["core_metrics"][key]["value"])
        self.assertEqual(model["ai_cognition"]["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
