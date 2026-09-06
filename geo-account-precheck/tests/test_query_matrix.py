"""Query Matrix, intent classification, and coverage tests."""

from __future__ import annotations

import copy
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.models.cognition import AIObservation
from engine.models.company import CompanyProfile
from engine.models.query import Query
from engine.query.intent import classify_query
from engine.query.matrix import QueryMatrix


class IntentClassificationTest(unittest.TestCase):
    def test_common_intents_are_classified(self) -> None:
        self.assertEqual(classify_query("A公司和B公司哪个好"), "comparison")
        self.assertEqual(classify_query("冷库工程有哪些值得推荐的公司"), "recommendation")
        self.assertEqual(classify_query("冷库设备怎么选"), "decision")
        self.assertEqual(classify_query("上海本地冷库工程厂家"), "local")
        self.assertEqual(classify_query("冷库设备不制冷怎么办"), "problem")
        self.assertEqual(classify_query("冷库设备报价"), "commercial")
        self.assertEqual(classify_query("冷库设备是什么"), "informational")

    def test_empty_query_is_unknown(self) -> None:
        self.assertEqual(classify_query(""), "unknown")


class QueryMatrixTest(unittest.TestCase):
    def test_builds_scenario_queries_from_keyword_directions(self) -> None:
        data = load_fixture()
        matrix = QueryMatrix().build(CompanyProfile.from_dict(data))
        self.assertGreaterEqual(matrix.queries, [])
        queries = [query.query for query in matrix.queries]
        self.assertIn("冷库选型", queries)
        self.assertIn("冷库工程厂家推荐", queries)
        self.assertTrue(all(query.query for query in matrix.queries))
        self.assertTrue(all(query.status == "INFERENCE" for query in matrix.queries))

    def test_deduplicates_identical_queries(self) -> None:
        data = copy.deepcopy(load_fixture())
        data["keyword_directions"] = ["冷库选型", "冷库选型"]
        matrix = QueryMatrix().build(CompanyProfile.from_dict(data))
        count = sum(1 for query in matrix.queries if query.query == "冷库选型")
        self.assertEqual(count, 1)

    def test_matrix_to_dict_contains_query_and_coverage(self) -> None:
        matrix = QueryMatrix([Query(query="冷库选型", intent="scenario")])
        payload = matrix.to_dict()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["coverage"]["status"], "UNKNOWN")

    def test_infers_candidates_when_no_keywords_given(self) -> None:
        data = load_fixture()
        data["keyword_directions"] = []
        matrix = QueryMatrix().build(CompanyProfile.from_dict(data))
        self.assertTrue(any("推荐" in query.query or "推荐" in query.root for query in matrix.queries))


class QueryCoverageTest(unittest.TestCase):
    def test_real_observations_drive_coverage(self) -> None:
        matrix = QueryMatrix([Query(query="冷库工程有哪些值得推荐的公司", intent="recommendation")])
        observations = [
            AIObservation(
                query="冷库工程有哪些值得推荐的公司",
                query_type="recommendation",
                company_mentioned=True,
                company_recommended=True,
                company_correctly_described=True,
                company_cited=True,
                status="observed",
                observation_mode="observed",
            )
        ]
        coverage = matrix.coverage(observations)
        self.assertEqual(coverage.status, "OBSERVED")
        self.assertEqual(coverage.score, 100)
        self.assertEqual(coverage.total, 1)

    def test_simulated_observations_do_not_count(self) -> None:
        matrix = QueryMatrix([Query(query="冷库工程有哪些值得推荐的公司", intent="recommendation")])
        observations = [
            AIObservation(
                query="冷库工程有哪些值得推荐的公司",
                company_recommended=True,
                status="simulated",
                observation_mode="simulated",
            )
        ]
        coverage = matrix.coverage(observations)
        self.assertEqual(coverage.status, "UNKNOWN")
        self.assertIsNone(coverage.score)
        self.assertEqual(coverage.total, 0)

    def test_no_observations_returns_unknown(self) -> None:
        coverage = QueryMatrix().coverage([])
        self.assertEqual(coverage.status, "UNKNOWN")
        self.assertIsNone(coverage.score)


if __name__ == "__main__":
    unittest.main()
