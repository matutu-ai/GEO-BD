"""Evidence graph construction."""

from __future__ import annotations

from ..models.entity import EntityProfile
from ..models.evidence import EvidenceGraph, EvidenceItem, _node_id


def build_evidence_graph(entity: EntityProfile, items: list[EvidenceItem]) -> EvidenceGraph:
    graph = EvidenceGraph()
    company_name = entity.get_value("name")
    if not company_name:
        return graph

    company_id = _node_id("company", company_name)
    graph.add_node(company_id, company_name, "company")

    mappings = [
        ("brands", "brand", "company", "owns"),
        ("products", "product", "company", "offers"),
        ("services", "service", "company", "offers"),
        ("customers", "customer", "company", "serves"),
        ("cases", "case", "company", "completed"),
        ("locations", "location", "company", "located_in"),
        ("certificates", "certificate", "certificate", "certifies"),
        ("patents", "patent", "company", "holds"),
        ("media", "media", "media", "mentions"),
        ("website", "website", "company", "has_website"),
        ("contacts", "contact", "company", "has_contact"),
        ("founders", "founder", "founder", "founded"),
        ("experts", "expert", "expert", "works_for"),
        ("reviews", "review", "review", "reviews"),
    ]
    for field_name, kind, source_kind, relation in mappings:
        for value in entity.get_values(field_name):
            node_id = _node_id(kind, value)
            graph.add_node(node_id, value, kind)
            if source_kind == "company":
                graph.add_edge(company_id, relation, node_id)
            else:
                graph.add_edge(node_id, relation, company_id)

    for item in items:
        graph.add_item(item)
        if item.entity and item.entity == company_name:
            graph.add_node(company_id, company_name, "company", [item.id])
        elif item.entity:
            entity_id = _node_id("entity", item.entity)
            graph.add_node(entity_id, item.entity, "entity", [item.id])
    return graph
