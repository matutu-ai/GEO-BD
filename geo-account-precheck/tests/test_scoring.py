"""Golden Case 001: five-category V1 GEO Score."""

from __future__ import annotations

import unittest

from skill_case_support import run_case


class ScoringGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = run_case()[1]

    def test_five_categories_are_explicit_and_bounded(self) -> None:
        score = self.report["geo_score"]
        self.assertEqual(score["status"], "COMPUTED")
        self.assertEqual(score["scale"], 100)
        self.assertEqual(set(score["categories"]), {"entity", "ai_visibility", "query_coverage", "evidence", "authority"})
        values = [item["value"] for item in score["categories"].values()]
        self.assertTrue(all(0 <= value <= 100 for value in values))
        self.assertEqual(score["total"], 58)
        self.assertLess(score["total"], 65)

    def test_missing_category_is_not_zero(self) -> None:
        score = run_case()[1]["geo_score"]
        self.assertEqual(score["missing_categories"], [])
        self.assertEqual(score["available_categories"], list(score["categories"]))


if __name__ == "__main__":
    unittest.main()
