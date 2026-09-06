"""Evidence graph, evidence items, and evidence verification results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common import normalize_source_type, normalize_status, stringify


@dataclass
class EvidenceItem:
    id: str = ""
    claim: str = ""
    entity: str = ""
    source: str = ""
    source_url: str = ""
    source_type: str = "unknown"
    date: str = ""
    confidence: int = 0
    verified: bool = False
    entity_match: bool = False
    verifiable: bool = False
    status: str = "FACT"
    conflicts_with: list[str] = field(default_factory=list)
    category: str = "evidence"

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> "EvidenceItem":
        claim = stringify(data.get("claim"))
        source = stringify(data.get("source"))
        status = "UNKNOWN" if not source else normalize_status(data.get("status"), fallback="FACT")
        return cls(
            id=str(data.get("id") or f"E{index + 1:03d}"),
            claim=claim,
            entity=stringify(data.get("entity")),
            source=source,
            source_url=stringify(data.get("source_url")),
            source_type=normalize_source_type(data.get("source_type")),
            date=stringify(data.get("date")),
            confidence=_int(data.get("confidence"), 0),
            verified=bool(data.get("verified", False)),
            entity_match=bool(data.get("entity_match", False)),
            verifiable=bool(data.get("verifiable", False)),
            status=status,
            conflicts_with=[str(x) for x in (data.get("conflicts_with") or [])],
            category=str(data.get("category") or data.get("domain") or "evidence").lower(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "claim": self.claim,
            "entity": self.entity,
            "source": self.source,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "date": self.date,
            "confidence": self.confidence,
            "verified": self.verified,
            "entity_match": self.entity_match,
            "verifiable": self.verifiable,
            "status": self.status,
            "conflicts_with": self.conflicts_with,
            "category": self.category,
        }


@dataclass
class EvidenceNode:
    id: str = ""
    label: str = ""
    kind: str = "entity"
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "kind": self.kind, "evidence_ids": self.evidence_ids}


@dataclass
class EvidenceEdge:
    source: str = ""
    relation: str = ""
    target: str = ""
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "relation": self.relation,
            "target": self.target,
            "evidence_ids": self.evidence_ids,
        }


@dataclass
class EvidenceGraph:
    nodes: list[EvidenceNode] = field(default_factory=list)
    edges: list[EvidenceEdge] = field(default_factory=list)
    items: list[EvidenceItem] = field(default_factory=list)

    def _node(self, node_id: str) -> EvidenceNode | None:
        return next((node for node in self.nodes if node.id == node_id), None)

    def add_node(self, node_id: str, label: str, kind: str, evidence_ids: list[str] | None = None) -> None:
        if not node_id:
            return
        node = self._node(node_id)
        if node is None:
            self.nodes.append(EvidenceNode(id=node_id, label=label, kind=kind, evidence_ids=list(evidence_ids or [])))
        else:
            for evidence_id in evidence_ids or []:
                if evidence_id not in node.evidence_ids:
                    node.evidence_ids.append(evidence_id)

    def add_edge(self, source: str, relation: str, target: str, evidence_ids: list[str] | None = None) -> None:
        if not source or not target:
            return
        existing = next(
            (edge for edge in self.edges if edge.source == source and edge.relation == relation and edge.target == target),
            None,
        )
        if existing is None:
            self.edges.append(
                EvidenceEdge(source=source, relation=relation, target=target, evidence_ids=list(evidence_ids or []))
            )
        else:
            for evidence_id in evidence_ids or []:
                if evidence_id not in existing.evidence_ids:
                    existing.evidence_ids.append(evidence_id)

    def add_item(self, item: EvidenceItem) -> None:
        self.items.append(item)
        if item.entity:
            self.add_node(_node_id("entity", item.entity), item.entity, "entity", [item.id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class EvidenceScore:
    score: int = 0
    item_count: int = 0
    verified_count: int = 0
    third_party_count: int = 0
    with_source_count: int = 0
    conflicts: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    status: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "item_count": self.item_count,
            "verified_count": self.verified_count,
            "third_party_count": self.third_party_count,
            "with_source_count": self.with_source_count,
            "conflicts": self.conflicts,
            "gaps": self.gaps,
            "checks": self.checks,
            "status": self.status,
        }


def _node_id(kind: str, label: str) -> str:
    safe = label.lower().replace(" ", "-").replace("（", "").replace("）", "")
    return f"{kind}:{safe}"


def _int(value: Any, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default
