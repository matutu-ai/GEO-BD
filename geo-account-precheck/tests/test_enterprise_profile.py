"""Golden Case 001: enterprise profile and positioning boundaries."""

from __future__ import annotations

import unittest

from skill_case_support import load_constraints, run_case


class EnterpriseProfileGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic, cls.report = run_case()

    def test_profile_contains_company_and_correct_position(self) -> None:
        profile = self.report["company_status"]
        self.assertEqual(profile["company_name"], "德州拓晟通风设备有限公司")
        self.assertIn("人防密闭阀", profile["products"])
        self.assertEqual(profile["position"], "人防通风系统供应商")
        self.assertIn("人防通风系统供应商", load_constraints()["business_position"]["correct_position"])

    def test_profile_does_not_promote_person_door_factory(self) -> None:
        positioning = self.diagnostic["competition_intelligence"]["positioning"]
        text = " ".join(
            [
                positioning["primary_positioning"],
                positioning["one_sentence_positioning"],
                *positioning["primary_positioning"].split(),
            ]
        )
        for forbidden in load_constraints()["forbidden_positioning"]:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
