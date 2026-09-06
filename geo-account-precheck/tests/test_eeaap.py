"""EEAAP scorer tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.eeaap.scorer import EeaapScorer
from engine.entity.researcher import EntityResearcher
from engine.evidence.verifier import EvidenceVerifier
from engine.models.company import CompanyProfile
from engine.models.entity import EntityProfile
from engine.models.evidence import EvidenceItem


class EeaapScorerTest(unittest.TestCase):
    def setUp(self) -> None:
        data = load_fixture()
        self.entity = EntityResearcher(mode="offline").research(CompanyProfile.from_dict(data))
        self.items = [EvidenceItem.from_dict(item, index) for index, item in enumerate(data["evidence"])]

    def test_scores_all_dimensions_between_zero_and_100(self) -> None:
        evidence_score = EvidenceVerifier().verify(self.items)
        result = EeaapScorer().score(self.entity, self.items, evidence_score.score)
        self.assertEqual(result["status"], "COMPUTED")
        for key in ("experience", "evidence", "authoritativeness", "accuracy", "perspective", "overall"):
            self.assertGreaterEqual(result[key], 0)
            self.assertLessEqual(result[key], 100)
        self.assertIn("basis", result)

    def test_empty_input_does_not_fake_computed_eeaap(self) -> None:
        result = EeaapScorer().score(EntityProfile(), [], None)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["overall"], 0)

    def test_claims_with_absolute_language_reduce_accuracy(self) -> None:
        items = [
            EvidenceItem(id="E1", claim="我们是行业第一", source="官网", source_type="official", status="FACT")
        ]
        result = EeaapScorer().score(EntityProfile(), items, 100)
        self.assertEqual(result["accuracy"], 0)
        self.assertTrue(any("Accuracy" in gap for gap in result["gaps"]))


if __name__ == "__main__":
    unittest.main()
