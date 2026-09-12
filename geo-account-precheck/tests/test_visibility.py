"""Golden Case 001: AI Visibility behavior."""

from __future__ import annotations

import unittest

from skill_case_support import run_case


class VisibilityGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic, cls.report = run_case()

    def test_real_observations_drive_visibility_metrics(self) -> None:
        ai = self.report["ai_cognition"]
        self.assertEqual(ai["status"], "OBSERVED")
        self.assertEqual(ai["observation_count"], 6)
        self.assertEqual(ai["brand_recognition"], 50)
        self.assertEqual(ai["recommend_probability"], 33)
        self.assertLess(ai["recommend_probability"], 50)

    def test_person_door_query_is_not_recommended(self) -> None:
        row = next(
            item
            for item in self.diagnostic["competition_intelligence"]["recommendation_decisions"]
            if item["query"] == "人防门厂家有哪些"
        )
        self.assertNotIn(row["recommendation"], {"Strong Recommendation", "Recommended"})
        self.assertLess(row["qualification_match"], 60)
        self.assertIn("资质尚未核验/未具备", row["reason"])


if __name__ == "__main__":
    unittest.main()
