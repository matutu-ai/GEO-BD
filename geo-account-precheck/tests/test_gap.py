"""GEO gap analyzer tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.common import UNKNOWN
from engine.entity.researcher import EntityResearcher
from engine.gap.analyzer import analyze_gaps
from engine.models.company import CompanyProfile
from engine.models.entity import EntityProfile
from engine.models.evidence import EvidenceScore
from engine.models.query import QueryCoverage
from engine.query.matrix import QueryMatrix


class GapAnalyzerTest(unittest.TestCase):
    def test_empty_input_creates_critical_entity_and_high_gaps(self) -> None:
        entity = EntityProfile()
        gaps = analyze_gaps(
            entity,
            EvidenceScore(),
            {"experience": 0, "authoritativeness": 0, "trustworthiness": 0},
            {"authoritativeness": 0, "trustworthiness": 0},
            QueryCoverage(status=UNKNOWN),
            QueryMatrix(),
            UNKNOWN,
            None,
            [],
        )
        types = [gap["type"] for gap in gaps["gaps"]]
        self.assertEqual(len(types), 10)
        self.assertIn("Entity Gap", types)
        self.assertIn("Query Gap", types)
        self.assertIn("Evidence Gap", types)
        self.assertIn("Competitor Gap", types)
        self.assertTrue(any(gap["type"] == "Entity Gap" and gap["severity"] == "critical" for gap in gaps["gaps"]))
        self.assertTrue(all(gap["severity"] in {"critical", "high", "medium", "low"} for gap in gaps["gaps"]))

    def test_complete_input_reduces_core_gap_severity(self) -> None:
        data = load_fixture()
        entity = EntityResearcher(mode="offline").research(CompanyProfile.from_dict(data))
        from engine.pipeline import build_evidence_items

        items = build_evidence_items(data)
        from engine.evidence.verifier import EvidenceVerifier

        evidence = EvidenceVerifier().verify(items)
        coverage = QueryCoverage(status="OBSERVED", score=100, citation_rate=100)
        gaps = analyze_gaps(
            entity,
            evidence,
            {"experience": 100, "authoritativeness": 100, "trustworthiness": 50},
            {"authoritativeness": 100, "trustworthiness": 50},
            coverage,
            QueryMatrix(),
            "COMPUTED",
            97,
            [],
        )
        entity_gap = next(item for item in gaps["gaps"] if item["type"] == "Entity Gap")
        self.assertNotEqual(entity_gap["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
