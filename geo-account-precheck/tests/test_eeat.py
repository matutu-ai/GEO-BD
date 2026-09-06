"""EEAT scorer tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.eeaap.scorer import EeaapScorer
from engine.eeat.scorer import EeatScorer
from engine.entity.researcher import EntityResearcher
from engine.evidence.verifier import EvidenceVerifier
from engine.models.company import CompanyProfile
from engine.models.entity import EntityProfile
from engine.models.evidence import EvidenceItem


class EeatScorerTest(unittest.TestCase):
    def setUp(self) -> None:
        data = load_fixture()
        self.entity = EntityResearcher(mode="offline").research(CompanyProfile.from_dict(data))
        self.items = [EvidenceItem.from_dict(item, index) for index, item in enumerate(data["evidence"])]

    def test_eeat_is_separate_from_eeaap(self) -> None:
        evidence = EvidenceVerifier().verify(self.items)
        eeaap = EeaapScorer().score(self.entity, self.items, evidence.score)
        result = EeatScorer().score(self.entity, self.items, evidence, eeaap)
        self.assertEqual(result["status"], "COMPUTED")
        for key in ("experience", "expertise", "authoritativeness", "trustworthiness", "overall"):
            self.assertGreaterEqual(result[key], 0)
            self.assertLessEqual(result[key], 100)
        self.assertIn("difference_from_eeaap", result)

    def test_empty_input_stays_unknown(self) -> None:
        evidence = EvidenceVerifier().verify([])
        eeaap = EeaapScorer().score(EntityProfile(), [], None)
        result = EeatScorer().score(EntityProfile(), [], evidence, eeaap)
        self.assertEqual(result["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
