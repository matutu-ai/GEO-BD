"""Competitor analyzer tests."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.common import UNKNOWN
from engine.competitor.analyzer import CompetitorAnalyzer
from engine.entity.researcher import EntityResearcher
from engine.models.company import CompanyProfile
from engine.models.competitor import Competitor
from engine.query.matrix import QueryMatrix


class CompetitorAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_fixture()
        self.company = CompanyProfile.from_dict(self.data)
        self.entity = EntityResearcher(mode="offline").research(self.company)
        self.matrix = QueryMatrix().build(self.company)
        self.client_scores = {
            "entity": 98,
            "query": 100,
            "local": 80,
            "evidence": 70,
            "authority": 80,
            "citation": 100,
            "recommendation": 100,
        }

    def test_no_competitors_are_not_invented(self) -> None:
        result = CompetitorAnalyzer("示例冷库设备公司").analyze([], self.entity, self.client_scores, self.matrix)
        self.assertEqual(result.status, UNKNOWN)
        self.assertEqual(result.competitors, [])
        self.assertIsNone(result.score)
        self.assertIn("不自动制造竞品", result.basis)

    def test_competitor_from_string_is_candidate_only(self) -> None:
        competitor = Competitor.from_dict("竞品A")
        self.assertEqual(competitor.name, "竞品A")
        self.assertEqual(competitor.status, "candidate")

    def test_confirmed_competitor_produces_computed_gap_matrix(self) -> None:
        data = copy.deepcopy(self.data)
        competitor = Competitor.from_dict(data["competitors"][0])
        result = CompetitorAnalyzer("示例冷库设备公司").analyze(
            [competitor], self.entity, self.client_scores, self.matrix
        )
        self.assertEqual(result.status, "COMPUTED")
        self.assertIsNotNone(result.score)
        self.assertEqual(len(result.gap_matrix), 10)
        computed = [gap for gap in result.gap_matrix if gap.status == "COMPUTED"]
        self.assertEqual(len(computed), 10)
        self.assertTrue(all(gap.gap is not None and 0 <= gap.gap <= 100 for gap in computed))

    def test_same_company_name_is_filtered_out(self) -> None:
        competitor = Competitor.from_dict({"name": "示例冷库设备公司", "status": "confirmed"})
        result = CompetitorAnalyzer("示例冷库设备公司").analyze([competitor], self.entity, self.client_scores, self.matrix)
        self.assertEqual(result.status, UNKNOWN)


if __name__ == "__main__":
    unittest.main()
