"""Validation evaluator tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.validation.evaluator import ValidationEvaluator


class ValidationEvaluatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = ValidationEvaluator()

    def test_no_after_data_is_unknown(self) -> None:
        result = self.evaluator.evaluate({"mention_rate": 30}, {})
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["improvement_score"])

    def test_improved_metrics_produce_improvement_score(self) -> None:
        result = self.evaluator.evaluate(
            {"mention_rate": 30, "recommendation_rate": 20, "query_coverage": 25},
            {"mention_rate": 60, "recommendation_rate": 50, "query_coverage": 40},
        )
        self.assertEqual(result["status"], "Improved")
        self.assertGreater(result["improvement_score"], 50)
        self.assertEqual(len(result["metric_changes"]), 3)

    def test_declined_metrics_are_flagged(self) -> None:
        result = self.evaluator.evaluate(
            {"mention_rate": 60, "recommendation_rate": 50},
            {"mention_rate": 30, "recommendation_rate": 20},
        )
        self.assertEqual(result["status"], "Declined")
        self.assertLess(result["improvement_score"], 50)

    def test_incomparable_after_data_stays_unknown(self) -> None:
        result = self.evaluator.evaluate({"mention_rate": 30}, {"unrelated_metric": 99})
        self.assertEqual(result["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
