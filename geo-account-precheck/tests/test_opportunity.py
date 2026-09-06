"""Opportunity scorer tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.common import UNKNOWN
from engine.gap.analyzer import analyze_gaps
from engine.models.entity import EntityProfile
from engine.models.evidence import EvidenceScore
from engine.models.query import QueryCoverage
from engine.models.scoring import Opportunity
from engine.query.matrix import QueryMatrix
from engine.scoring.opportunity import OpportunityScorer


class OpportunityScorerTest(unittest.TestCase):
    def test_scores_all_opportunities_with_valid_ranges(self) -> None:
        gaps = analyze_gaps(
            EntityProfile(),
            EvidenceScore(),
            {"experience": 0, "authoritativeness": 0, "trustworthiness": 0},
            {"authoritativeness": 0, "trustworthiness": 0},
            QueryCoverage(status=UNKNOWN),
            QueryMatrix(),
            UNKNOWN,
            None,
            [],
        )
        result = OpportunityScorer().score(gaps["gaps"], [], {})
        self.assertEqual(result["count"], len(result["opportunities"]))
        self.assertTrue(result["opportunities"])
        for item in result["opportunities"]:
            self.assertTrue(0 <= item["score"] <= 100)
            self.assertIn(item["priority"], {"P0", "P1", "P2"})
            self.assertTrue(0 <= item["business_value"] <= 100)
            self.assertTrue(0 <= item["feasibility"] <= 100)
        self.assertTrue(any(item["priority"] == "P0" for item in result["opportunities"]))

    def test_priority_thresholds(self) -> None:
        self.assertEqual(Opportunity.priority_for(85), "P0")
        self.assertEqual(Opportunity.priority_for(60), "P1")
        self.assertEqual(Opportunity.priority_for(40), "P2")
        self.assertEqual(Opportunity.priority_for(34), "P3")


if __name__ == "__main__":
    unittest.main()
