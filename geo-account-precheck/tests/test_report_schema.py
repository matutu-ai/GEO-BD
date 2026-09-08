"""Schema tests for the V3 ReportModel JSON contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import ROOT, load_fixture, run_diagnostic

from engine.reporting import build_report_model
from engine.validation.schema_validator import validate_against_schema_file


class ReportSchemaTest(unittest.TestCase):
    def test_full_sample_model_matches_report_schema(self) -> None:
        model = build_report_model(run_diagnostic(load_fixture())).to_dict()
        self.assertEqual(validate_against_schema_file(model, ROOT / "schemas" / "report.schema.json"), [])

    def test_empty_input_model_matches_report_schema(self) -> None:
        model = build_report_model(run_diagnostic({})).to_dict()
        self.assertEqual(validate_against_schema_file(model, ROOT / "schemas" / "report.schema.json"), [])

    def test_model_matches_each_report_level_schema(self) -> None:
        model = build_report_model(run_diagnostic(load_fixture())).to_dict()
        for name in ("executive", "operational", "technical"):
            errors = validate_against_schema_file(model, ROOT / "schemas" / f"{name}-report.schema.json")
            self.assertEqual(errors, [], f"{name}-report.schema.json errors: {errors}")


if __name__ == "__main__":
    unittest.main()
