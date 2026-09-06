"""End-to-end tests for the full GEO diagnostic pipeline."""

from __future__ import annotations

import unittest

from support import load_fixture, render, run_diagnostic, validate_diagnostic


EXPECTED_HEADINGS = [
    "## 01 Executive Summary",
    "## 02 Company Entity",
    "## 03 AI Cognition",
    "## 04 Query Intelligence",
    "## 05 Competitor Intelligence",
    "## 06 Evidence Graph",
    "## 07 EEAAP",
    "## 08 EEAT",
    "## 09 Scenario Coverage",
    "## 10 Keyword Coverage",
    "## 11 AI Test",
    "## 12 NAP / Trust",
    "## 13 GEO Gap",
    "## 14 GEO Opportunity",
    "## 15 P0/P1/P2/P3 Action Plan",
    "## 16 Next Test",
    "## 17 Validation Plan",
    "## 18 Data Quality",
    "## 19 Unknown / Missing Data",
]


class EndToEndDiagnosticTest(unittest.TestCase):
    def test_full_sample_produces_complete_diagnostic(self) -> None:
        result = run_diagnostic(load_fixture())
        self.assertEqual(validate_diagnostic(result), [])

        self.assertEqual(result["meta"]["engine"], "GEO Diagnostic Engine")
        self.assertEqual(result["entity"]["research_mode"], "offline")
        self.assertTrue(result["entity"]["fields"])
        self.assertEqual(result["ai_cognition"]["status"], "OBSERVED")
        self.assertEqual(result["query_matrix"]["coverage"]["status"], "OBSERVED")
        self.assertEqual(result["competitors"]["status"], "COMPUTED")
        self.assertTrue(result["evidence_graph"]["items"])
        self.assertIn("experience", result["eeaap"])
        self.assertIn("trustworthiness", result["eeat"])
        self.assertTrue(result["gaps"]["gaps"])
        self.assertTrue(result["opportunities"]["opportunities"])
        self.assertTrue(result["recommendations"]["actions"])
        self.assertTrue(result["validation"])
        self.assertFalse(result["data_quality"]["low_quality"])
        self.assertGreaterEqual(result["data_quality"]["score"], 50)

        scores = result["scores"]
        self.assertIsNotNone(scores["entity_score"])
        self.assertIsNotNone(scores["ai_cognition_score"])
        self.assertIsNotNone(scores["query_coverage_score"])
        self.assertIsNotNone(scores["evidence_score"])
        self.assertIsNotNone(scores["eeaap_score"])
        self.assertIsNotNone(scores["eeat_score"])
        self.assertIsNotNone(scores["competitor_gap_score"])
        self.assertIsNotNone(scores["geo_score"])
        for score in scores.values():
            if isinstance(score, int):
                self.assertTrue(0 <= score <= 100)

    def test_report_renders_all_fourteen_headings(self) -> None:
        markdown = render(run_diagnostic(load_fixture()))
        headings = [line for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, EXPECTED_HEADINGS)

    def test_empty_input_is_low_quality_and_unknown(self) -> None:
        result = run_diagnostic({})
        self.assertEqual(validate_diagnostic(result), [])
        self.assertTrue(result["data_quality"]["low_quality"])
        self.assertEqual(result["data_quality"]["score"], 0)
        self.assertIn("可信度有限", result["data_quality"]["warning"])
        self.assertEqual(result["ai_cognition"]["status"], "UNKNOWN")
        self.assertEqual(result["competitors"]["status"], "UNKNOWN")
        self.assertEqual(result["validation"]["status"], "UNKNOWN")
        self.assertIn("补充", render(result))


if __name__ == "__main__":
    unittest.main()
