"""GEO-BD V3 regression: 德州拓晟通风设备有限公司.

Verifies that regulated product keywords such as 人防门 never upgrade an
explicitly absent qualification to verified, and that qualification-gated
queries stay out of the recommended bands.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from support import run_diagnostic, validate_against_schema_file, validate_diagnostic  # noqa: E402


CASE_ROOT = Path(__file__).resolve().parent / "cases" / "dezhou-tuosheng"
ROOT = CASE_ROOT.parents[2]


def load_case() -> dict:
    return json.loads((CASE_ROOT / "company.json").read_text(encoding="utf-8"))


class DezhouTuoshengRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_diagnostic(load_case())
        cls.ci = cls.result["competition_intelligence"]

    def _decision(self, query: str) -> dict | None:
        return next(
            (item for item in self.ci["recommendation_decisions"] if item["query"] == query),
            None,
        )

    def test_fixture_passes_full_schema(self) -> None:
        self.assertEqual(validate_diagnostic(self.result), [])
        self.assertEqual(
            validate_against_schema_file(
                self.ci,
                ROOT / "schemas" / "competition-intelligence.schema.json",
            ),
            [],
        )

    def test_qualification_boundary_does_not_invent_person_door_certificate(self) -> None:
        boundary = {item["item"]: item for item in self.ci["qualification_boundary"]}
        self.assertEqual(boundary["人防门定点生产资质"]["status"], "absent")
        self.assertEqual(boundary["人防门定点生产资质"]["risk_level"], "medium")
        self.assertEqual(boundary["建筑机电安装工程专业承包资质"]["status"], "unverified")
        self.assertFalse(
            any(
                item["status"] == "verified" and "人防门" in item["item"]
                for item in self.ci["qualification_boundary"]
            )
        )

    def test_keyword_presence_does_not_upgrade_qualification_to_verified(self) -> None:
        # Catalog keyword 人防门 must not upgrade the qualification to verified.
        safety = {item["claim"]: item for item in self.ci["claim_safety"]}
        claim = next(
            item["claim"]
            for item in self.ci["claim_safety"]
            if "人防门定点生产资质" in item["claim"] and "不代表" in item["claim"]
        )
        self.assertIn(safety[claim]["status"], {"UNVERIFIED", "FACT"})
        for query in ("人防门厂家", "人防门定点生产厂家"):
            with self.subTest(query=query):
                self.assertLessEqual(self._decision(query)["qualification_match"], 10)

    def test_positive_ventilation_queries_are_recommended(self) -> None:
        expected = {
            "人防通风设备厂家": 75,
            "人防密闭阀厂家": 75,
            "油网滤尘器厂家": 75,
            "过滤吸收器厂家": 75,
            "人防通风系统集成": 90,
            "河南人防通风项目": 75,
        }
        for query, minimum in expected.items():
            with self.subTest(query=query):
                decision = self._decision(query)
                self.assertIsNotNone(decision, f"缺少决策行: {query}")
                self.assertGreaterEqual(decision["score"], minimum)
                self.assertIn(
                    decision["recommendation"],
                    {"Strong Recommendation", "Recommended"},
                )

    def test_qualification_gated_queries_are_not_recommended(self) -> None:
        restricted = {
            "人防门定点生产厂家",
            "需要完整人防门定点资质",
            "需要厂家独立出具人防门完整验收资料",
        }
        for query in restricted:
            with self.subTest(query=query):
                decision = self._decision(query)
                self.assertIsNotNone(decision, f"缺少决策行: {query}")
                self.assertNotIn(
                    decision["recommendation"],
                    {"Strong Recommendation", "Recommended"},
                )
                self.assertLess(decision["qualification_match"], 60)
                self.assertIn("资质尚未核验/未具备", decision["reason"])

    def test_person_door_scenario_is_restricted(self) -> None:
        scenario = next(
            item
            for item in self.ci["customer_scenarios"]
            if item["scenario"] == "需要人防门"
        )
        self.assertFalse(scenario["recommended"])
        self.assertLess(scenario["qualification_match"], 60)
        self.assertTrue(any("定点/生产资质尚未核验" in limit for limit in scenario["limitations"]))


if __name__ == "__main__":
    unittest.main()
