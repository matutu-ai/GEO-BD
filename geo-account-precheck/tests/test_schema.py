"""JSON Schema validation tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import ROOT, load_fixture, run_diagnostic, validate_against_schema_file, validate_diagnostic

from engine.validation.schema_validator import SchemaValidator


class SchemaValidatorTest(unittest.TestCase):
    def test_diagnostic_report_from_full_sample_matches_schema(self) -> None:
        result = run_diagnostic(load_fixture())
        self.assertEqual(validate_diagnostic(result), [])
        self.assertEqual(
            validate_against_schema_file(
                result["competition_intelligence"],
                ROOT / "schemas" / "competition-intelligence.schema.json",
            ),
            [],
        )

    def test_competition_intelligence_schema_rejects_invalid_recommendation_score(self) -> None:
        result = run_diagnostic(load_fixture())
        scenario = result["competition_intelligence"]["customer_scenarios"][0]
        scenario["recommendation_score"] = 101
        errors = validate_against_schema_file(
            result["competition_intelligence"],
            ROOT / "schemas" / "competition-intelligence.schema.json",
        )
        self.assertTrue(any("expected <= 100" in error for error in errors))

    def test_diagnostic_report_from_empty_input_still_matches_schema(self) -> None:
        result = run_diagnostic({})
        self.assertEqual(validate_diagnostic(result), [])

    def test_missing_top_level_key_is_detected(self) -> None:
        result = run_diagnostic(load_fixture())
        del result["scores"]
        self.assertTrue(any("missing required property 'scores'" in error for error in validate_diagnostic(result)))

    def test_external_ref_resolves_evidence_schema(self) -> None:
        schema = {"$ref": "evidence.schema.json"}
        validator = SchemaValidator(schema, base_dir=ROOT / "schemas")
        self.assertEqual(
            validator.validate(
                {
                    "id": "E1",
                    "claim": "真实声明",
                    "status": "FACT",
                    "source_type": "third_party",
                    "confidence": 90,
                }
            ),
            [],
        )
        errors = validator.validate({"id": "E1", "claim": 123, "status": "MAYBE"})
        self.assertTrue(any("expected string" in error for error in errors))
        self.assertTrue(any("one of" in error for error in errors))

    def test_external_ref_resolves_cognition_with_internal_definitions(self) -> None:
        schema = {"$ref": "cognition.schema.json"}
        validator = SchemaValidator(schema, base_dir=ROOT / "schemas")
        errors = validator.validate(
            {
                "observation_mode": "observed",
                "status": "OBSERVED",
                "observations": [{"status": "observed"}],
                "count": 1,
                "basis": "真实观察",
            }
        )
        self.assertTrue(any("$.observations[0]" in error and "missing required property 'query'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
