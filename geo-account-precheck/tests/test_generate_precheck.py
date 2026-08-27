from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_precheck import (  # noqa: E402
    build_issue_audit,
    build_report,
    missing_eeaap_keys,
    missing_required_fields,
    render_checklist,
    render_input_template,
    render_prompts,
)


class GeneratePrecheckTest(unittest.TestCase):
    def test_report_contains_required_sections(self) -> None:
        report = build_report(
            {
                "company": "示例冷库设备公司",
                "business": "冷库设备工程厂家",
                "customers": "冷链物流、食品加工企业",
                "materials": "官网、资质、三个项目案例",
                "current_ai_cognition": "AI 能识别主营方向",
                "negative_publicity": "未发现重大负面",
                "keyword_directions": ["冷库造价与方案", "冷库维护与故障", "冷库供应商选择"],
                "evidence": {
                    "experience": "三个已交付项目",
                    "evidence": "设备参数、现场照片",
                    "authoritativeness": "行业资质",
                    "accuracy": "参数可核验",
                    "perspective": "适用场景与局限已写清",
                },
            }
        )
        for section in ("## 1. 资料自查", "## 2. 账户画像与关键词", "## 3. EEAAP 检测", "## 4. 行动清单"):
            self.assertIn(section, report)
        self.assertIn("冷库造价与方案", report)
        self.assertIn("Experience", report)

    def test_missing_eeaap_is_detected(self) -> None:
        missing = missing_eeaap_keys({"evidence": {"experience": "项目证据"}})
        self.assertIn("Evidence", missing)
        self.assertIn("Accuracy", missing)

    def test_missing_required_fields_is_detected(self) -> None:
        missing = missing_required_fields({"company": "示例公司"})
        self.assertIn("business", missing)
        self.assertIn("customers", missing)
        self.assertNotIn("company", missing)

    def test_input_template_contains_execution_fields(self) -> None:
        template = render_input_template()
        self.assertIn('"company"', template)
        self.assertIn('"keyword_directions"', template)
        self.assertIn('"evidence"', template)

    def test_prompt_pack_contains_key_blocks(self) -> None:
        prompts = render_prompts()
        self.assertIn("[资料自查]", prompts)
        self.assertIn("[账户画像九大板块]", prompts)
        self.assertIn("[场景关键词]", prompts)
        self.assertIn("[EEAAP 检测]", prompts)

    def test_checklist_contains_publishing_invariants(self) -> None:
        checklist = render_checklist()
        self.assertIn("[发布策略]", checklist)
        self.assertIn("意图场景 → 问答场景 → 品牌场景", checklist)
        self.assertIn("60-80", checklist)
        self.assertIn("[电话/官网露出]", checklist)

    def test_issue_audit_flags_phone_and_overall_issues(self) -> None:
        report = build_issue_audit(
            {
                "company": "示例公司",
                "issues": ["电话/官网露出不理想", "账户整体场景报表数据不理想"],
            }
        )
        self.assertIn("## 2. 电话/官网露出排查", report)
        self.assertIn("## 3. 整体场景报表排查", report)
        self.assertIn("全网NAP一致性", report)
        self.assertIn("反问 AI", report)

    def test_cli_check_returns_nonzero_when_evidence_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            input_path.write_text(json.dumps({"company": "示例公司"}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "generate_precheck.py"), "--input", str(input_path), "--check"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISSING_EVIDENCE", result.stderr)

    def test_cli_template_writes_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "input.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_precheck.py"),
                    "--template",
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertIn("evidence", data)
        self.assertIn("keyword_directions", data)


if __name__ == "__main__":
    unittest.main()
