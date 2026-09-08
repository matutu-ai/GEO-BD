"""Operational (L2) report renderer tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture, run_diagnostic

from engine.reporting import build_report_model, generate_report


class OperationalReportTest(unittest.TestCase):
    def test_full_sample_report_exposes_share_and_conflict(self) -> None:
        diagnostic = run_diagnostic(load_fixture())
        model = build_report_model(diagnostic)
        markdown = generate_report(diagnostic, "operational", model)
        self.assertIn("# GEO Operational Report", markdown)
        self.assertIn("## 04 Competitor", markdown)
        self.assertIn("| 示例冷库设备公司 | 50% | 1 |", markdown)
        self.assertIn("| 竞品A | 50% | 1 |", markdown)
        self.assertIn("发现需要建立 Canonical Source 的证据或 NAP 冲突", markdown)
        self.assertIn("## 08 Opportunity", markdown)
        self.assertIn("## 09 Action Plan", markdown)

    def test_entity_diagnostic_gaps_still_appear_without_observations(self) -> None:
        payload = {
            "company": {
                "name": "只做实体诊断测试企业",
                "business": "冷库设备",
                "products": ["组合式冷库"],
                "services": ["冷库设计"],
            },
            "ai_observations": [],
            "competitors": [
                {
                    "name": "竞品A",
                    "status": "confirmed",
                    "mention_rate": 90,
                    "recommendation_rate": 80,
                    "citation_rate": 50,
                    "sources": ["用户上报"],
                }
            ],
            "evidence": [],
        }
        diagnostic = run_diagnostic(payload)
        model = build_report_model(diagnostic)
        markdown = generate_report(diagnostic, "operational", model)
        self.assertIn("UNKNOWN：没有真实 AI Observation，无法计算 AI Share of Voice", markdown)
        self.assertIn("| 竞品A | confirmed | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |", markdown)
        self.assertIn("| UNKNOWN | - | - | - | UNKNOWN |", markdown)
        self.assertIn("## 05 Entity Consistency", markdown)
        self.assertIn("## 09 Action Plan", markdown)


if __name__ == "__main__":
    unittest.main()
