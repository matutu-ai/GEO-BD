"""Evidence and NAP conflict handling tests in the ReportModel."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture, run_diagnostic

from engine.reporting import InsightEngine


class ConflictHandlingTest(unittest.TestCase):
    def test_conflicting_evidence_items_are_flagged(self) -> None:
        diagnostic = {
            "evidence_graph": {
                "items": [
                    {
                        "id": "E1",
                        "claim": "客户数 20,000",
                        "source": "来源A",
                    },
                    {
                        "id": "E2",
                        "claim": "客户数 100,000",
                        "source": "来源B",
                        "conflicts_with": ["E1"],
                    },
                ]
            }
        }
        conflicts = InsightEngine(diagnostic).build().to_dict()["evidence_conflicts"]
        self.assertEqual(conflicts["status"], "CONFLICT")
        self.assertEqual(conflicts["count"], 1)
        row = conflicts["conflicts"][0]
        self.assertEqual(row["evidence_id"], "E2")
        self.assertEqual(row["conflicts_with"], ["E1"])
        self.assertEqual(row["source"], "来源B")

    def test_evidence_without_conflicts_is_none(self) -> None:
        diagnostic = {
            "evidence_graph": {
                "items": [
                    {"id": "E1", "claim": "客户数 20,000", "source": "来源A"},
                    {"id": "E2", "claim": "持有资质", "source": "来源B"},
                ]
            }
        }
        conflicts = InsightEngine(diagnostic).build().to_dict()["evidence_conflicts"]
        self.assertEqual(conflicts["status"], "NONE")
        self.assertEqual(conflicts["conflicts"], [])

    def test_sample_nap_conflict_surfaces_in_report(self) -> None:
        model = InsightEngine(run_diagnostic(load_fixture())).build().to_dict()
        self.assertEqual(model["evidence_conflicts"]["status"], "CONFLICT")
        self.assertIn("NAP", model["evidence_conflicts"]["conflicts"][0]["evidence_id"])

    def test_no_evidence_means_no_conflict_claim(self) -> None:
        conflicts = InsightEngine(run_diagnostic({})).build().to_dict()["evidence_conflicts"]
        self.assertEqual(conflicts["status"], "UNKNOWN")
        self.assertEqual(conflicts["conflicts"], [])


if __name__ == "__main__":
    unittest.main()
