"""Executable boundary tests for the GEO-BD Standard Diagnostic Contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from engine.validation.schema_validator import validate_against_schema_file


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "diagnostic.schema.json"
STATUS_VALUES = {
    "VERIFIED",
    "OBSERVED",
    "PROVIDED",
    "INFERRED",
    "UNKNOWN",
    "NOT_RUN",
    "INSUFFICIENT_DATA",
}
FORBIDDEN_EXECUTION_FIELDS = {
    "generated_keywords",
    "generated_personas",
    "generated_content",
    "publishing_plan",
    "media_plan",
    "generated_market_queries",
    "target_market_queries",
    "plan_30_60_90",
    "operating_plan_30_60_90",
}


def standard_contract() -> dict[str, Any]:
    return {
        "contract_version": "1.0.0",
        "meta": {
            "diagnostic_id": "diagnostic-001",
            "engine": "GEO-BD",
            "generated_at": "2026-09-18T00:00:00+08:00",
            "status": "INFERRED",
            "input_snapshot_id": "snapshot-001",
            "notes": [],
        },
        "facts": [
            {
                "id": "FACT-company-name",
                "subject": "企业",
                "predicate": "名称",
                "value": "示例企业",
                "status": "PROVIDED",
                "source_ids": ["SOURCE-client-001"],
                "observed_at": None,
                "notes": None,
            }
        ],
        "evidence_verification": [
            {
                "id": "EVID-company-name",
                "fact_id": "FACT-company-name",
                "status": "VERIFIED",
                "method": "公开登记信息交叉核验",
                "source_ids": ["SOURCE-registry-001"],
                "conclusion": "名称一致",
                "conflicts": [],
            }
        ],
        "diagnostic_measurements": [
            {
                "id": "METRIC-evidence-coverage",
                "name": "Evidence Coverage",
                "value": 100,
                "unit": "percent",
                "status": "INFERRED",
                "fact_ids": ["FACT-company-name"],
                "evidence_ids": ["EVID-company-name"],
                "basis": "唯一示例事实已有核验记录",
            }
        ],
        "judgments": [
            {
                "id": "JUDGMENT-evidence-present",
                "statement": "示例事实具备可追溯核验记录",
                "status": "INFERRED",
                "source_fact_ids": [],
                "source_metric_ids": ["METRIC-evidence-coverage"],
                "basis": "Evidence Coverage 为 100",
                "confidence": 1.0,
            }
        ],
        "root_causes": [
            {
                "id": "ROOT-no-evidence-gap",
                "statement": "该示例未发现名称证据缺口",
                "status": "INFERRED",
                "judgment_ids": ["JUDGMENT-evidence-present"],
                "basis": "判断已确认核验链完整",
            }
        ],
        "prescriptions": [
            {
                "id": "PRESCRIPTION-maintain-source-trace",
                "statement": "保持企业名称来源可追溯",
                "status": "INFERRED",
                "root_cause_ids": ["ROOT-no-evidence-gap"],
                "priority": "P2",
                "expected_outcome": "后续诊断继续引用同一事实来源",
                "verification_method": "复核 Fact 与 Evidence 引用关系",
                "handoff_to": "GEO",
            }
        ],
        "report_projection": {
            "source_contract_version": "1.0.0",
            "status": "INFERRED",
            "title": "客户 GEO 快速诊断",
            "customer_positioning": {
                "one_sentence": "示例企业是一家提供示例业务的服务商",
                "core_business": ["示例业务"],
                "main_customers": ["企业客户"],
                "main_scenarios": ["企业采购"],
                "source_ids": ["FACT-company-name"],
            },
            "ai_geo_status": {
                "summary": "目前已有基础事实与核验记录，其他 AI / GEO 状态仍需真实观察。",
                "source_ids": ["METRIC-evidence-coverage", "JUDGMENT-evidence-present"],
            },
            "main_problems": [
                {
                    "problem": "真实 AI 观察资料不足",
                    "source_ids": ["JUDGMENT-evidence-present"],
                }
            ],
            "optimization_directions": {
                "P0": [],
                "P1": [],
                "P2": [
                    {
                        "direction": "保持企业基础事实来源可追溯，并交由 GEO 执行后续优化",
                        "prescription_ids": ["PRESCRIPTION-maintain-source-trace"],
                    }
                ],
            },
            "diagnostic_basis": [
                {"statement": "企业名称由客户提供", "source_ids": ["FACT-company-name"]},
                {"statement": "企业名称已有核验记录", "source_ids": ["EVID-company-name"]},
                {"statement": "示例事实核验覆盖率为 100%", "source_ids": ["METRIC-evidence-coverage"]},
            ],
        },
    }


def contract_integrity_errors(contract: dict[str, Any]) -> list[str]:
    """Checks cross-record references and null semantics not handled by the local schema subset."""
    errors: list[str] = []
    facts = {item["id"] for item in contract.get("facts", [])}
    evidence = {item["id"] for item in contract.get("evidence_verification", [])}
    metrics = {item["id"] for item in contract.get("diagnostic_measurements", [])}
    judgments = {item["id"] for item in contract.get("judgments", [])}
    roots = {item["id"] for item in contract.get("root_causes", [])}
    prescriptions = {item["id"] for item in contract.get("prescriptions", [])}

    for item in contract.get("facts", []):
        if item.get("status") in {"VERIFIED", "OBSERVED", "PROVIDED"} and not item.get("source_ids"):
            errors.append(f"{item.get('id')}: sourced fact requires source_ids")
        if item.get("status") == "UNKNOWN" and item.get("value") is not None:
            errors.append(f"{item.get('id')}: UNKNOWN fact value must be null")

    for item in contract.get("evidence_verification", []):
        if item.get("fact_id") not in facts:
            errors.append(f"{item.get('id')}: unknown Fact ID")

    unavailable = {"UNKNOWN", "NOT_RUN", "INSUFFICIENT_DATA"}
    for item in contract.get("diagnostic_measurements", []):
        fact_ids = set(item.get("fact_ids", []))
        evidence_ids = set(item.get("evidence_ids", []))
        if not fact_ids and not evidence_ids:
            errors.append(f"{item.get('id')}: metric requires Fact or Evidence reference")
        if not fact_ids.issubset(facts):
            errors.append(f"{item.get('id')}: unknown Fact ID")
        if not evidence_ids.issubset(evidence):
            errors.append(f"{item.get('id')}: unknown Evidence ID")
        if item.get("status") in unavailable and item.get("value") is not None:
            errors.append(f"{item.get('id')}: unavailable metric value must be null")

    for item in contract.get("judgments", []):
        fact_ids = set(item.get("source_fact_ids", []))
        metric_ids = set(item.get("source_metric_ids", []))
        if not fact_ids and not metric_ids:
            errors.append(f"{item.get('id')}: Judgment requires Fact or Metric reference")
        if not fact_ids.issubset(facts) or not metric_ids.issubset(metrics):
            errors.append(f"{item.get('id')}: Judgment reference does not exist")

    for item in contract.get("root_causes", []):
        judgment_ids = set(item.get("judgment_ids", []))
        if not judgment_ids or not judgment_ids.issubset(judgments):
            errors.append(f"{item.get('id')}: Root Cause requires existing Judgment ID")

    for item in contract.get("prescriptions", []):
        root_ids = set(item.get("root_cause_ids", []))
        if not root_ids or not root_ids.issubset(roots):
            errors.append(f"{item.get('id')}: Prescription requires existing Root Cause ID")

    report_sources = facts | evidence | metrics | judgments | roots | prescriptions
    projection = contract.get("report_projection", {})
    projected_items = [
        projection.get("customer_positioning", {}),
        projection.get("ai_geo_status", {}),
        *projection.get("main_problems", []),
        *projection.get("diagnostic_basis", []),
    ]
    for item in projected_items:
        source_ids = set(item.get("source_ids", []))
        if not source_ids or not source_ids.issubset(report_sources):
            errors.append("Report Projection requires existing source ID")

    problems = projection.get("main_problems", [])
    if len(problems) > 5:
        errors.append("Report Projection allows at most five main problems")
    basis = projection.get("diagnostic_basis", [])
    if not 3 <= len(basis) <= 5:
        errors.append("Report Projection requires three to five diagnostic basis items")

    for priority in ("P0", "P1", "P2"):
        for direction in projection.get("optimization_directions", {}).get(priority, []):
            prescription_ids = set(direction.get("prescription_ids", []))
            if not prescription_ids or not prescription_ids.issubset(prescriptions):
                errors.append(f"{priority} direction requires existing Prescription ID")
    return errors


def all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for nested in value.values():
            keys.update(all_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(all_keys(nested))
    return keys


class ProductBoundaryContractTest(unittest.TestCase):
    def test_standard_contract_matches_canonical_schema_and_reference_chain(self) -> None:
        contract = standard_contract()
        self.assertEqual(validate_against_schema_file(contract, SCHEMA_PATH), [])
        self.assertEqual(contract_integrity_errors(contract), [])

    def test_canonical_schema_has_one_status_vocabulary(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["definitions"]["status"]["enum"]), STATUS_VALUES)

    def test_parallel_machine_status_is_rejected(self) -> None:
        contract = standard_contract()
        contract["meta"]["status"] = "DERIVED"
        errors = validate_against_schema_file(contract, SCHEMA_PATH)
        self.assertTrue(any("value must be one of" in error for error in errors))

    def test_standard_output_contains_no_keyword_persona_or_content_generation(self) -> None:
        keys = all_keys(standard_contract())
        self.assertTrue(FORBIDDEN_EXECUTION_FIELDS.isdisjoint(keys))

    def test_public_report_has_only_the_fixed_one_page_structure(self) -> None:
        projection = standard_contract()["report_projection"]
        self.assertEqual(
            set(projection),
            {
                "source_contract_version",
                "status",
                "title",
                "customer_positioning",
                "ai_geo_status",
                "main_problems",
                "optimization_directions",
                "diagnostic_basis",
            },
        )
        self.assertEqual(set(projection["optimization_directions"]), {"P0", "P1", "P2"})

    def test_standard_output_rejects_publishing_media_query_and_fixed_timeline_plans(self) -> None:
        for field in FORBIDDEN_EXECUTION_FIELDS:
            with self.subTest(field=field):
                contract = standard_contract()
                contract[field] = {}
                errors = validate_against_schema_file(contract, SCHEMA_PATH)
                self.assertTrue(any(f"unexpected property '{field}'" in error for error in errors))

    def test_prescription_must_reference_existing_root_cause(self) -> None:
        contract = standard_contract()
        contract["prescriptions"][0]["root_cause_ids"] = ["ROOT-missing"]
        self.assertTrue(any("Prescription requires" in error for error in contract_integrity_errors(contract)))

    def test_root_cause_must_reference_existing_judgment(self) -> None:
        contract = standard_contract()
        contract["root_causes"][0]["judgment_ids"] = []
        self.assertTrue(any("Root Cause requires" in error for error in contract_integrity_errors(contract)))

    def test_judgment_must_reference_fact_or_metric(self) -> None:
        contract = standard_contract()
        contract["judgments"][0]["source_fact_ids"] = []
        contract["judgments"][0]["source_metric_ids"] = []
        self.assertTrue(any("Judgment requires" in error for error in contract_integrity_errors(contract)))

    def test_unknown_measurement_cannot_become_zero(self) -> None:
        contract = standard_contract()
        contract["diagnostic_measurements"][0]["status"] = "UNKNOWN"
        contract["diagnostic_measurements"][0]["value"] = 0
        self.assertTrue(any("value must be null" in error for error in contract_integrity_errors(contract)))

    def test_not_run_measurement_cannot_become_one_hundred(self) -> None:
        contract = standard_contract()
        contract["diagnostic_measurements"][0]["status"] = "NOT_RUN"
        contract["diagnostic_measurements"][0]["value"] = 100
        self.assertTrue(any("value must be null" in error for error in contract_integrity_errors(contract)))

    def test_report_projection_cannot_contain_diagnostic_calculation(self) -> None:
        contract = standard_contract()
        contract["report_projection"].update({"score": 88, "gap": "new gap", "agent_trace": []})
        errors = validate_against_schema_file(contract, SCHEMA_PATH)
        for field in ("score", "gap", "agent_trace"):
            self.assertTrue(any(f"unexpected property '{field}'" in error for error in errors))

    def test_public_report_limits_problems_and_basis(self) -> None:
        contract = standard_contract()
        contract["report_projection"]["main_problems"] *= 6
        self.assertTrue(any("at most five" in error for error in contract_integrity_errors(contract)))

        contract = standard_contract()
        contract["report_projection"]["diagnostic_basis"] = contract["report_projection"]["diagnostic_basis"][:2]
        self.assertTrue(any("three to five" in error for error in contract_integrity_errors(contract)))

    def test_public_report_directions_must_reference_internal_prescriptions(self) -> None:
        contract = standard_contract()
        contract["report_projection"]["optimization_directions"]["P1"] = [
            {"direction": "无依据方向", "prescription_ids": ["PRESCRIPTION-missing"]}
        ]
        self.assertTrue(any("direction requires" in error for error in contract_integrity_errors(contract)))


if __name__ == "__main__":
    unittest.main()
