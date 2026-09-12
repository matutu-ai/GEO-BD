"""Golden Case 001: Evidence audit behavior."""

from __future__ import annotations

import unittest

from skill_case_support import run_case


class EvidenceGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic, cls.report = run_case()

    def test_evidence_is_present_but_still_weakly_verified(self) -> None:
        evidence = self.report["evidence_trust"]
        self.assertEqual(evidence["count"], 4)
        self.assertEqual(evidence["verified_count"], 0)
        self.assertEqual(evidence["third_party_count"], 0)
        self.assertEqual(evidence["score"], 60)
        self.assertTrue(evidence["gaps"])

    def test_qualification_boundary_keeps_missing_certificate_unverified(self) -> None:
        boundaries = {
            item["item"]: item
            for item in self.diagnostic["competition_intelligence"]["qualification_boundary"]
        }
        item = boundaries["人防门防护设备定点生产"]
        self.assertEqual(item["status"], "absent")
        self.assertNotEqual(item["status"], "verified")


if __name__ == "__main__":
    unittest.main()
