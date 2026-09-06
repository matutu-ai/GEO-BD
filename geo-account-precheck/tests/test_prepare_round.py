"""CLI tests for the next-round input preparation script."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIAGNOSTIC = ROOT / "scripts" / "run_diagnostic.py"
PREPARE_ROUND = ROOT / "scripts" / "prepare_round.py"
SAMPLE = ROOT / "tests" / "fixtures" / "sample_company.json"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class PrepareRoundCliTest(unittest.TestCase):
    def _round1_report(self, tmp: str) -> Path:
        report_path = Path(tmp) / "round1.json"
        result = _run(RUN_DIAGNOSTIC, "--input", str(SAMPLE), "--json", str(report_path), "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        return report_path

    def test_next_round_keeps_static_facts_and_clears_measurements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = self._round1_report(tmp)
            next_path = Path(tmp) / "round2.json"
            result = _run(PREPARE_ROUND, "--from", str(report_path), "--out", str(next_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PREPARED_ROUND", result.stdout)

            data = json.loads(next_path.read_text(encoding="utf-8"))
            self.assertEqual(data["company"]["name"], "示例冷库设备公司")
            self.assertEqual(data["company"]["business"], "冷库设备工程")
            self.assertEqual(data["materials"], ["官网", "资质证书", "三个项目案例", "设备参数表"])
            self.assertEqual(data["ai_observations"], [])
            self.assertEqual(data["competitors"], [])
            self.assertEqual(data["evidence"], [])
            self.assertEqual(data["current_metrics"], {})
            self.assertEqual(data["validation"], {})


if __name__ == "__main__":
    unittest.main()
