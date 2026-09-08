"""Technical (L3) report renderer and V2 compatibility tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture, run_diagnostic

from engine.reporting import build_report_model, generate_report, render_legacy_report


class TechnicalReportTest(unittest.TestCase):
    def test_technical_report_keeps_full_legacy_19_chapter_view(self) -> None:
        diagnostic = run_diagnostic(load_fixture())
        model = build_report_model(diagnostic)
        markdown = generate_report(diagnostic, "technical", model)
        self.assertEqual(markdown, render_legacy_report(diagnostic))
        self.assertIn("# GEO Diagnostic Report", markdown)
        self.assertIn("Engine：GEO Diagnostic Engine 3.0.0", markdown)
        self.assertIn("## 19 Unknown / Missing Data", markdown)


if __name__ == "__main__":
    unittest.main()
