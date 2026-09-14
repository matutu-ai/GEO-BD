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

    def build_growth(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        """Build the V3 growth prescription handoff from all existing results."""

        company = diagnostic.get("company") or {}
        diagnosis = diagnostic.get("diagnosis_summary") or {}
        gap_result = diagnostic.get("geo_gap") or {}
        gap_items = gap_result.get("gaps") or []
        problems = _unique([str(item.get("problem")) for item in gap_items if item.get("problem")])
        if not problems:
            problems = [UNKNOWN]
        actions = [
            _action("P0", "企业AI定位校准", "先统一企业身份、业务角色和边界，避免 AI 误解企业。", gap_items),
            _action("P1", "企业信息资产完善", "补齐 AI 理解企业所需的基础事实和业务关系。", gap_items),
            _action("P1", "信任与案例资产补充", "补充可核验的经验、资质和信任依据。", gap_items),
            _action("P2", "专业能力表达建设", "让企业专业能力和应用价值形成稳定认知。", gap_items),
        ]
        score = diagnostic.get("growth_score") or {}
        score_text = score.get("total") if score.get("total") is not None else UNKNOWN
        return {
            "company": str(company.get("name") or UNKNOWN),
            "current_status": str(
                f"{diagnosis.get('current_stage') or UNKNOWN}；GEO Score {score_text}/100。"
            ),
            "main_problem": str(
                (diagnosis.get("core_problems") or [UNKNOWN])[0]
            ),
            "problems": problems[:8],
            "priority_actions": actions,
            "priority_tasks": [item["task"] for item in actions],
            "recommended_actions": [item["action"] for item in actions],
            "30_days": "完成企业AI定位校准和基础信息资产补齐。",
            "60_days": "完成专业能力、案例经验和信任资产补充。",
            "90_days": "用同一批真实 AI 场景复测认知变化，再交接 GEO 执行层。",
            "boundary": "只输出诊断后的增长处方，不负责内容生产或长期运营执行。",
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


def _action(priority: str, task: str, action: str, gaps: list[dict[str, Any]]) -> dict[str, Any]:
    related = [str(item.get("reason")) for item in gaps if item.get("reason")][:2]
    return {
        "priority": priority,
        "task": task,
        "action": action,
        "basis": related or [UNKNOWN],
    }


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
