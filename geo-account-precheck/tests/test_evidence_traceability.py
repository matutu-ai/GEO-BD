"""Evidence traceability tests for ReportModel rows."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture, run_diagnostic

from engine.reporting import build_report_model


class EvidenceTraceabilityTest(unittest.TestCase):
    def test_full_sample_evidence_refs_keep_source_metadata(self) -> None:
        model = build_report_model(run_diagnostic(load_fixture())).to_dict()
        refs = model["evidence_refs"]
        self.assertEqual([ref["id"] for ref in refs], ["E001", "E002", "E003", "E004", "E005"])
        for ref in refs:
            self.assertTrue(ref["claim"])
            self.assertTrue(ref["source"])
            self.assertTrue(ref["date"])
            self.assertTrue(ref["status"])

    def test_problems_and_actions_reference_existing_evidence(self) -> None:
        model = build_report_model(run_diagnostic(load_fixture())).to_dict()
        evidence_ids = {ref["id"] for ref in model["evidence_refs"]}
        self.assertTrue(any(problem["evidence_ids"] for problem in model["top_problems"]))
        for block in (model["top_problems"], model["opportunities"], model["action_plan"]):
            for row in block:
                self.assertTrue(set(row["evidence_ids"]).issubset(evidence_ids))

    def test_empty_input_has_no_traceable_evidence(self) -> None:
        model = build_report_model(run_diagnostic({})).to_dict()
        self.assertEqual(model["evidence_refs"], [])
        for block in (model["top_problems"], model["opportunities"], model["action_plan"]):
            for row in block:
                self.assertEqual(row["evidence_ids"], [])


if __name__ == "__main__":
    unittest.main()
