"""Recommendation planner tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.gap.analyzer import analyze_gaps
from engine.models.entity import EntityProfile
from engine.models.evidence import EvidenceScore
from engine.models.query import QueryCoverage
from engine.query.matrix import QueryMatrix
from engine.recommendation.planner import RecommendationPlanner
from engine.scoring.opportunity import OpportunityScorer


class RecommendationPlannerTest(unittest.TestCase):
    def test_every_opportunity_has_executable_action(self) -> None:
        gaps = analyze_gaps(
            EntityProfile(),
            EvidenceScore(),
            {"experience": 0, "authoritativeness": 0, "trustworthiness": 0},
            {"authoritativeness": 0, "trustworthiness": 0},
            QueryCoverage(status="UNKNOWN"),
            QueryMatrix(),
            "UNKNOWN",
            None,
            [],
        )
        opportunities = OpportunityScorer().score(gaps["gaps"], [], {})["opportunities"]
        plan = RecommendationPlanner().plan(gaps["gaps"], opportunities)
        self.assertEqual(plan["count"], len(opportunities))
        self.assertEqual(plan["count"], len(plan["actions"]))
        for action in plan["actions"]:
            self.assertTrue(action["task"])
            self.assertTrue(action["action"])
            self.assertTrue(action["required_materials"])
            self.assertTrue(action["verification"])
            self.assertIn(action["priority"], {"P0", "P1", "P2"})

    def test_priority_is_preserved_from_opportunity(self) -> None:
        opportunities = [
            {
                "title": "补充真实客户案例",
                "score": 90,
                "priority": "P0",
                "reason": "高价值动作",
                "status": "INFERENCE",
                "basis": "测试",
            }
        ]
        plan = RecommendationPlanner().plan([], opportunities)
        self.assertEqual(plan["actions"][0]["priority"], "P0")
        self.assertIn("验收资料", plan["actions"][0]["required_materials"])


if __name__ == "__main__":
    unittest.main()
