"""Golden Case 001: Query Matrix and content gaps."""

from __future__ import annotations

import unittest

from skill_case_support import run_case


class QueryGapGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic, cls.report = run_case()

    def test_query_types_and_observations_are_visible(self) -> None:
        query = self.report["query_coverage"]
        self.assertEqual(query["status"], "OBSERVED")
        self.assertEqual(query["total"], 8)
        self.assertEqual(query["observed"], 6)
        self.assertEqual({item["type"] for item in query["by_type"]}, {"brand", "business", "scenario", "commercial"})
        self.assertEqual(query["score"], 44)

    def test_required_content_gaps_are_detected(self) -> None:
        gaps = self.report["geo_gaps"]
        text = " ".join(str(item) for item in gaps)
        for expected in ("人防通风系统解决方案", "人防工程验收资料", "密闭阀选型指南"):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
