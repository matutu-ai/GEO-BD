"""Boundary tests for the real-data / UNKNOWN / NOT_RUN rules."""

from __future__ import annotations

import copy
import unittest

from support import load_fixture, render, run_diagnostic, validate_diagnostic


class DiagnosticBoundaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_fixture()

    def test_empty_input_stays_unknown_without_invented_rates(self) -> None:
        result = run_diagnostic({})
        self.assertEqual(validate_diagnostic(result), [])
        self.assertEqual(result["ai_cognition"]["status"], "UNKNOWN")
        self.assertEqual(result["query_matrix"]["coverage"]["status"], "UNKNOWN")
        self.assertEqual(result["scenarios"]["status"], "UNKNOWN")
        self.assertEqual(result["scenarios"]["scenario_status"], "UNKNOWN")
        self.assertEqual(result["scenarios"]["keyword_status"], "UNKNOWN")
        self.assertIsNone(result["scenarios"]["keyword_coverage"])
        self.assertIsNone(result["scenarios"]["keyword_coverage_score"])
        self.assertEqual(result["citations"]["status"], "NOT_RUN")
        self.assertIsNone(result["citations"]["citation_rate"])
        self.assertEqual(result["ai_tests"]["status"], "NOT_RUN")
        self.assertTrue(result["ai_tests"]["insufficient_data"])
        self.assertEqual(result["competitors"]["status"], "UNKNOWN")
        self.assertEqual(result["competitors"]["competitors"], [])
        self.assertIsNone(result["competitors"]["score"])
        self.assertEqual(result["scores"]["status"], "INSUFFICIENT_DATA")
        for key in ("geo_score", "entity_score", "ai_cognition_score", "evidence_score", "keyword_coverage_score"):
            self.assertIsNone(result["scores"][key])

    def test_full_company_without_real_ai_observations_never_scores_keywords(self) -> None:
        data = copy.deepcopy(self.data)
        data["ai_observations"] = []
        data["competitors"] = []
        result = run_diagnostic(data)
        self.assertEqual(validate_diagnostic(result), [])

        self.assertEqual(result["ai_cognition"]["status"], "UNKNOWN")
        self.assertEqual(result["query_matrix"]["coverage"]["status"], "UNKNOWN")
        self.assertEqual(result["scenarios"]["status"], "NOT_RUN")
        self.assertEqual(result["scenarios"]["scenario_status"], "NOT_RUN")
        self.assertEqual(result["scenarios"]["keyword_status"], "NOT_RUN")
        self.assertIsNone(result["scenarios"]["scenario_coverage"])
        self.assertIsNone(result["scenarios"]["keyword_coverage"])
        self.assertIsNone(result["scenarios"]["scenario_coverage_score"])
        self.assertIsNone(result["scenarios"]["keyword_coverage_score"])
        self.assertIsNone(result["keywords"]["coverage"])

        self.assertEqual(result["citations"]["status"], "NOT_RUN")
        for rate in ("mention_rate", "recommendation_rate", "citation_rate"):
            self.assertIsNone(result["citations"][rate])
        self.assertEqual(result["ai_tests"]["status"], "NOT_RUN")
        self.assertTrue(result["ai_tests"]["insufficient_data"])
        self.assertEqual(result["ai_tests"]["total"], 0)
        for rate in ("mention_rate", "recommendation_rate", "citation_rate"):
            self.assertIsNone(result["ai_tests"][rate])

        for key in ("ai_cognition_score", "query_coverage_score", "scenario_coverage_score", "keyword_coverage_score", "citation_score"):
            self.assertIsNone(result["scores"][key])

        markdown = render(result)
        self.assertIn("Keyword 状态：NOT_RUN", markdown)
        self.assertIn("Keyword Coverage：UNKNOWN", markdown)
        self.assertIn("Citation Rate：UNKNOWN", markdown)
        self.assertNotIn("Keyword Coverage：50", markdown)

    def test_empty_competitor_list_is_not_invented(self) -> None:
        data = copy.deepcopy(self.data)
        data["competitors"] = []
        result = run_diagnostic(data)
        self.assertEqual(validate_diagnostic(result), [])
        self.assertEqual(result["competitors"]["status"], "UNKNOWN")
        self.assertEqual(result["competitors"]["competitors"], [])
        self.assertEqual(result["competitors"]["gap_matrix"], [])
        self.assertIsNone(result["competitors"]["score"])
        self.assertIn("不自动制造竞品", result["competitors"]["basis"])
        self.assertIsNone(result["scores"]["competitor_gap_score"])

    def test_evidence_without_source_stays_unknown(self) -> None:
        data = copy.deepcopy(self.data)
        data["ai_observations"] = []
        data["competitors"] = []
        data["evidence"] = [
            {
                "id": "E-NO-SOURCE",
                "claim": "这条声明没有任何可追溯来源",
                "status": "FACT",
            }
        ]
        result = run_diagnostic(data)
        self.assertEqual(validate_diagnostic(result), [])
        item = result["evidence_graph"]["items"][0]
        self.assertEqual(item["id"], "E-NO-SOURCE")
        self.assertEqual(item["source"], "")
        self.assertEqual(item["source_type"], "unknown")
        self.assertEqual(item["status"], "UNKNOWN")

    def test_simulated_and_raw_observations_do_not_become_rates(self) -> None:
        data = copy.deepcopy(self.data)
        data["competitors"] = []
        data["evidence"] = []
        data["ai_observations"] = [
            {
                "query": "冷库工程有哪些值得推荐的公司",
                "query_type": "recommendation",
                "company_recommended": True,
                "observation_mode": "simulated",
                "status": "simulated",
            },
            {
                "query": "冷库工程厂家推荐",
                "query_type": "scenario",
                "company_mentioned": True,
                "observation_mode": "raw",
                "status": "raw",
            },
        ]
        result = run_diagnostic(data)
        self.assertEqual(validate_diagnostic(result), [])
        self.assertEqual(result["ai_cognition"]["status"], "UNKNOWN")
        self.assertEqual(result["query_matrix"]["coverage"]["status"], "UNKNOWN")
        self.assertEqual(result["scenarios"]["status"], "NOT_RUN")
        self.assertIsNone(result["scenarios"]["keyword_coverage"])
        self.assertIsNone(result["scenarios"]["keyword_coverage_score"])
        self.assertEqual(result["citations"]["status"], "NOT_RUN")
        self.assertIsNone(result["citations"]["citation_rate"])
        self.assertEqual(result["ai_tests"]["status"], "NOT_RUN")
        self.assertTrue(result["ai_tests"]["insufficient_data"])
        self.assertIsNone(result["ai_tests"]["mention_rate"])
        self.assertIsNone(result["scores"]["ai_cognition_score"])
        self.assertIsNone(result["scores"]["query_coverage_score"])
        self.assertIsNone(result["scores"]["keyword_coverage_score"])
        self.assertIsNone(result["scores"]["citation_score"])


if __name__ == "__main__":
    unittest.main()
