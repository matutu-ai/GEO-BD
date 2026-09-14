"""Generate module-level GEO prescriptions from an AI diagnosis summary."""

from __future__ import annotations

from typing import Any


UNKNOWN = "【需客户补充真实资料】"

PRESCRIPTIONS = (
    ("P1", "企业AI定位优化", "让 AI 准确理解企业身份。", "企业AI定位描述"),
    ("P1", "企业信息资产完善", "提升 AI 对企业业务的理解。", "企业知识基础资料"),
    ("P2", "专业内容建设", "增强 AI 对企业专业能力的判断。", "专业能力资料"),
    ("P2", "信任体系建设", "提升 AI 推荐企业时的可信依据。", "企业信任资料库"),
)


class PrescriptionAgent:
    """Turn diagnosis problems into a bounded GEO handoff."""

    def build(self, diagnosis: dict[str, Any]) -> dict[str, Any]:
        problems = diagnosis.get("core_problems") or [UNKNOWN]
        return {
            "company_position": str(diagnosis.get("company_position") or UNKNOWN),
            "current_stage": str(diagnosis.get("current_stage") or UNKNOWN),
            "prescriptions": [
                {
                    "priority": priority,
                    "title": title,
                    "goal": goal,
                    "problem": _problem_for(index, problems),
                    "output": output,
                }
                for index, (priority, title, goal, output) in enumerate(PRESCRIPTIONS)
            ],
            "next_step": "进入 GEO 优化执行流程。",
            "boundary": "只输出需要解决的能力模块；具体执行交给后续 GEO。",
        }


def render_geo_prescription(prescription: dict[str, Any]) -> str:
    """Render a prescription without keyword or content-production details."""

    lines = [
        "# GEO优化处方",
        "",
        f"当前阶段：{prescription.get('current_stage') or UNKNOWN}",
        "",
    ]
    for item in prescription.get("prescriptions") or []:
        lines.extend(
            [
                f"## 优先级 {item.get('priority', 'UNKNOWN')}",
                "",
                f"### {item.get('title') or UNKNOWN}",
                "",
                f"目标：{item.get('goal') or UNKNOWN}",
                "",
                f"需要解决：{item.get('problem') or UNKNOWN}",
                "",
                f"交付物：{item.get('output') or UNKNOWN}",
                "",
            ]
        )
    lines.extend(
        [
            "## 下一步",
            "",
            str(prescription.get("next_step") or UNKNOWN),
            "",
            f"边界：{prescription.get('boundary') or UNKNOWN}",
            "",
        ]
    )
    return "\n".join(lines)


def _problem_for(index: int, problems: list[Any]) -> str:
    return str(problems[index]) if index < len(problems) else UNKNOWN
