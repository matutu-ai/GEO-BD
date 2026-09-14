"""Contract tests for the user-facing interaction prompt layer."""

from __future__ import annotations

import unittest

from interaction import available_stages, render_prompt


class InteractionPromptTest(unittest.TestCase):
    def test_all_stages_have_renderable_prompts(self) -> None:
        self.assertEqual(
            available_stages(),
            ("welcome", "intake", "diagnosis", "competition", "visibility", "personas", "prescription", "report"),
        )
        for stage in available_stages():
            output = render_prompt(stage)
            self.assertTrue(output.startswith("# "), stage)
            self.assertNotIn("{{", output, stage)

    def test_dynamic_values_are_injected_and_lists_are_readable(self) -> None:
        output = render_prompt(
            "visibility",
            {
                "brand_recognition": "40%",
                "business_understanding": "55%",
                "trust_level": "需补充真实观察",
                "recommend_probability": "30%",
                "visibility_stage": "KNOWN",
                "visibility_summary": "AI 已识别企业，但推荐依据不足。",
            },
        )
        self.assertIn("40%", output)
        self.assertIn("KNOWN", output)
        self.assertNotIn("【需企业补充真实资料】", output)

    def test_missing_data_is_explicit_and_unknown_stage_is_rejected(self) -> None:
        self.assertIn("【需企业补充真实资料】", render_prompt("report"))
        with self.assertRaises(ValueError):
            render_prompt("unknown")


if __name__ == "__main__":
    unittest.main()
