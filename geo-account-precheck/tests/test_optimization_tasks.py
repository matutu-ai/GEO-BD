"""Acceptance tests for module-level AI cognition improvement tasks."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agents.optimization_task_agent import render_optimization_tasks
from engine.pipeline import DiagnosticPipeline
from engine.validation.schema_validator import validate_against_schema_file
from skill_case_support import CASE_ROOT, ROOT, load_case


TASK_SCHEMA = ROOT / "schemas" / "optimization_task_schema.json"


class OptimizationTaskAgentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(load_case())
        cls.tasks = cls.diagnostic["optimization_tasks"]
        cls.markdown = render_optimization_tasks(cls.tasks)

    def test_tasks_match_schema_and_fixed_module_order(self) -> None:
        self.assertEqual(validate_against_schema_file(self.tasks, TASK_SCHEMA), [])
        self.assertEqual(self.tasks["module"], "AI认知提升任务")
        self.assertEqual(
            [task["title"] for task in self.tasks["tasks"]],
            [
                "企业定位校准任务",
                "企业信息资产补充任务",
                "专业内容建设任务",
                "信任信息增强任务",
                "AI搜索适配准备任务",
            ],
        )
        self.assertEqual([task["priority"] for task in self.tasks["tasks"]], ["P1", "P1", "P2", "P2", "P3"])

    def test_tasks_are_module_handoff_not_keyword_tasks(self) -> None:
        titles = " ".join(task["title"] for task in self.tasks["tasks"])
        self.assertNotIn("关键词", titles)
        self.assertNotIn("词包", titles)
        self.assertNotIn("文章题目", titles)
        self.assertIn("具体词包", self.tasks["next_step"]["handoff"])
        self.assertIn("GEO Strategy", self.tasks["next_step"]["handoff"])
        self.assertIn("企业AI定位描述", self.markdown)
        self.assertIn("企业信任资料库", self.markdown)

    def test_unknown_ai_state_is_not_presented_as_identified(self) -> None:
        data = load_case()
        data["ai_observations"] = []
        diagnostic = DiagnosticPipeline(offline=True, research_mode="offline").run(data)
        task_result = diagnostic["optimization_tasks"]
        self.assertIn("【需客户补充真实资料】", task_result["diagnosis"])
        self.assertIn("【需客户补充真实资料】", task_result["tasks"][0]["basis"][0])

    def test_cli_writes_module_task_exports(self) -> None:
        script = ROOT / "scripts" / "run_diagnostic.py"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "tasks.md"
            structured = Path(tmp) / "tasks.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--input",
                    str(CASE_ROOT / "company.json"),
                    "--offline",
                    "--optimization-tasks",
                    str(output),
                    "--optimization-tasks-json",
                    str(structured),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Top P1: 企业定位校准任务", result.stdout)
            self.assertEqual(
                validate_against_schema_file(json.loads(structured.read_text(encoding="utf-8")), TASK_SCHEMA),
                [],
            )
            self.assertIn("# GEO优化任务建议", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
