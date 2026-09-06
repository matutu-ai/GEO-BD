"""Evidence graph and verifier tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.entity.researcher import EntityResearcher
from engine.evidence.graph import build_evidence_graph
from engine.evidence.verifier import EvidenceVerifier
from engine.models.company import CompanyProfile
from engine.models.evidence import EvidenceItem


class EvidenceGraphTest(unittest.TestCase):
    def setUp(self) -> None:
        data = load_fixture()
        self.entity = EntityResearcher(mode="offline").research(CompanyProfile.from_dict(data))
        self.items = [EvidenceItem.from_dict(item, index) for index, item in enumerate(data["evidence"])]

    def test_graph_contains_company_nodes_and_expected_relations(self) -> None:
        graph = build_evidence_graph(self.entity, self.items)
        payload = graph.to_dict()
        relations = {(edge["source"], edge["relation"], edge["target"]) for edge in payload["edges"]}
        self.assertTrue(any(source.endswith("示例冷库设备公司") and relation == "offers" for source, relation, _ in relations))
        self.assertTrue(any(relation == "completed" for _, relation, _ in relations))
        self.assertTrue(any(relation == "serves" for _, relation, _ in relations))
        self.assertTrue(any(relation == "certifies" for _, relation, _ in relations))
        self.assertTrue(any(relation == "founded" for _, relation, _ in relations))
        self.assertGreaterEqual(len(payload["nodes"]), 15)
        self.assertEqual(len(payload["items"]), len(self.items))

    def test_empty_entity_returns_empty_graph(self) -> None:
        graph = build_evidence_graph(EntityResearcher(mode="offline").research(CompanyProfile.from_dict({})), [])
        self.assertEqual(graph.to_dict()["nodes"], [])


class EvidenceVerifierTest(unittest.TestCase):
    def test_no_evidence_returns_unknown(self) -> None:
        result = EvidenceVerifier().verify([])
        self.assertEqual(result.status, "UNKNOWN")
        self.assertTrue(result.gaps)

    def test_well_sourced_evidence_scores_high(self) -> None:
        items = [
            EvidenceItem(
                id="E1",
                claim="项目已验收",
                source="第三方检测报告",
                source_type="third_party",
                date="2026-01-01",
                confidence=90,
                verified=True,
                status="FACT",
            )
        ]
        result = EvidenceVerifier().verify(items)
        self.assertEqual(result.status, "COMPUTED")
        self.assertEqual(result.item_count, 1)
        self.assertGreaterEqual(result.score, 80)

    def test_conflict_no_source_and_exaggeration_are_flagged(self) -> None:
        items = [
            EvidenceItem(id="E1", claim="我们做到行业最好", source="", source_type="user_provided", verified=False),
            EvidenceItem(id="E2", claim="另一条冲突表述", source="官网", source_type="official", verified=True, conflicts_with=["E1"]),
        ]
        result = EvidenceVerifier().verify(items)
        self.assertIn("E1", result.conflicts)
        self.assertTrue(any("缺少来源" in gap for gap in result.gaps))
        self.assertTrue(any("夸张或绝对化" in gap for gap in result.gaps))
        self.assertFalse(result.checks["all_have_source"])
        self.assertFalse(result.checks["no_conflicts"])


if __name__ == "__main__":
    unittest.main()
