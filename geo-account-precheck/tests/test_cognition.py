"""Cognition analyzer and standard query bank tests."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.cognition.analyzer import CognitionAnalyzer
from engine.cognition.query_builder import build_cognition_queries
from engine.entity.researcher import EntityResearcher
from engine.models.company import CompanyProfile
from engine.query.matrix import QueryMatrix


class CognitionAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_fixture()
        self.company = CompanyProfile.from_dict(self.data)
        self.entity = EntityResearcher(mode="offline").research(self.company)

    def test_real_observation_yields_observed_score(self) -> None:
        observations = CognitionAnalyzer.observations_from_input(self.data, self.company)
        cognition = CognitionAnalyzer(self.company, self.entity).analyze(observations, QueryMatrix().build(self.company))
        self.assertEqual(cognition["observation_mode"], "observed")
        self.assertEqual(cognition["status"], "OBSERVED")
        self.assertIsNotNone(cognition["score"])

    def test_simulated_observation_stays_unknown(self) -> None:
        data = copy.deepcopy(self.data)
        data["ai_observations"] = [
            {
                "query": "冷库工程有哪些值得推荐的公司",
                "query_type": "recommendation",
                "company_recommended": True,
                "observation_mode": "simulated",
            }
        ]
        company = CompanyProfile.from_dict(data)
        observations = CognitionAnalyzer.observations_from_input(data, company)
        cognition = CognitionAnalyzer(company, EntityResearcher(mode="offline").research(company)).analyze(
            observations, QueryMatrix().build(company)
        )
        self.assertEqual(cognition["observation_mode"], "simulated")
        self.assertEqual(cognition["status"], "UNKNOWN")
        self.assertIsNone(cognition["score"])
        self.assertIn("不把模拟结果写成真实认知评分", cognition["basis"])

    def test_missing_observation_is_not_invented(self) -> None:
        data = copy.deepcopy(self.data)
        data["ai_observations"] = []
        company = CompanyProfile.from_dict(data)
        observations = CognitionAnalyzer.observations_from_input(data, company)
        cognition = CognitionAnalyzer(company, EntityResearcher(mode="offline").research(company)).analyze(
            observations, QueryMatrix().build(company)
        )
        self.assertEqual(cognition["observation_mode"], "UNKNOWN")
        self.assertEqual(cognition["status"], "UNKNOWN")
        self.assertIsNone(cognition["score"])

    def test_unknown_nonstructured_observation_is_not_counted_as_real(self) -> None:
        data = copy.deepcopy(self.data)
        data["ai_observations"] = ["AI 说了一些内容但没有结构化结果"]
        company = CompanyProfile.from_dict(data)
        observations = CognitionAnalyzer.observations_from_input(data, company)
        cognition = CognitionAnalyzer(company, EntityResearcher(mode="offline").research(company)).analyze(
            observations, QueryMatrix().build(company)
        )
        self.assertEqual(cognition["status"], "UNKNOWN")


class QueryBankTest(unittest.TestCase):
    def test_query_bank_contains_brand_and_recommendation_queries(self) -> None:
        data = load_fixture()
        company = CompanyProfile.from_dict(data)
        entity = EntityResearcher(mode="offline").research(company)
        queries = build_cognition_queries(company, entity)
        self.assertTrue(any("示例冷库设备公司是做什么的" == query["query"] for query in queries))
        self.assertTrue(any("冷库工程有哪些值得推荐的公司" == query["query"] for query in queries))
        self.assertTrue(all(query["query_type"] for query in queries))


if __name__ == "__main__":
    unittest.main()
