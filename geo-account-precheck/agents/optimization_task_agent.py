"""Generate module-level GEO improvement tasks from existing diagnostics.

This agent is intentionally a handoff layer. It does not create keywords,
content plans, rankings, or new company facts.
"""

from __future__ import annotations

from typing import Any


UNKNOWN = "【需客户补充真实资料】"
REAL_MODES = {"observed", "provided"}
TASK_IDS = {
    "企业定位校准任务": "task_01_positioning",
    "企业信息资产补充任务": "task_02_information",
    "专业内容建设任务": "task_03_professional",
    "信任信息增强任务": "task_04_trust",
    "AI搜索适配准备任务": "task_05_search_readiness",
}


class OptimizationTaskAgent:
    """Turn diagnostic gaps into capability modules for GEO operators."""

    def build(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": "GEO优化任务建议",
            "module": "AI认知提升任务",
            "diagnosis": _diagnosis(diagnostic),
            "tasks": [
                _positioning_task(diagnostic),
                _information_task(diagnostic),
                _professional_task(diagnostic),
                _trust_task(diagnostic),
                _search_readiness_task(diagnostic),
            ],
            "next_step": {
                "title": "进入 GEO 优化流程",
                "handoff": "本模块完成能力缺口交接；具体词包、内容矩阵和运营策略由后续 GEO Strategy 处理。",
            },
            "boundary": "只输出下一步应补齐的能力模块，不生成关键词任务、内容方案或发布排期。",
        }


def render_optimization_tasks(result: dict[str, Any]) -> str:
    """Render the operator-facing module task list."""

    lines = [
        "# GEO优化任务建议",
        "",
        "## AI认知提升任务",
        "",
        f"当前诊断：{_text(result.get('diagnosis'))}",
        "",
    ]
    for index, task in enumerate(result.get("tasks") or [], start=1):
        lines.extend(
            [
                f"## 优化任务 {index:02d}",
                "",
                f"### {task.get('priority', 'UNKNOWN')}｜{_text(task.get('title'))}",
                "",
                f"任务目标：{_text(task.get('goal'))}",
                "",
                "需要完善：",
                "",
                *[f"- {item}" for item in task.get("needs") or [UNKNOWN]],
                "",
                f"输出：{_text(task.get('output'))}",
                "",
            ]
        )
    next_step = result.get("next_step") or {}
    lines.extend(
        [
            "## 下一步",
            "",
            f"{_text(next_step.get('title'))}",
            "",
            f"{_text(next_step.get('handoff'))}",
            "",
            f"边界：{_text(result.get('boundary'))}",
            "",
        ]
    )
    return "\n".join(lines)


def _diagnosis(diagnostic: dict[str, Any]) -> str:
    observations = _real_observations(diagnostic)
    if not observations:
        return f"{UNKNOWN} 当前没有真实 AI 观察，不能判断 AI 已经识别企业；需要先补齐真实观察和企业基础信息。"
    ai_tests = diagnostic.get("ai_tests") or {}
    mention = _rate(ai_tests.get("mention_rate"))
    recommendation = _rate(ai_tests.get("recommendation_rate"))
    entity_score = _score((diagnostic.get("scores") or {}).get("entity_score"))
    return (
        f"当前 AI 已形成部分企业识别（提及率 {mention}），但推荐表现为 {recommendation}，"
        f"企业实体完整度为 {entity_score}；定位、专业能力和信任依据尚未形成稳定认知。"
    )


def _positioning_task(diagnostic: dict[str, Any]) -> dict[str, Any]:
    return _task(
        "P1",
        "企业定位校准任务",
        "建立 AI 对企业身份的准确理解。",
        ["企业行业定位", "企业业务角色", "核心服务能力", "差异化优势"],
        "企业AI定位描述",
        diagnostic,
        ("Entity Gap", "Content Gap"),
    )


def _information_task(diagnostic: dict[str, Any]) -> dict[str, Any]:
    return _task(
        "P1",
        "企业信息资产补充任务",
        "提升 AI 对企业业务的理解深度。",
        ["企业介绍", "产品体系", "服务范围", "技术能力", "应用场景"],
        "企业知识基础资料",
        diagnostic,
        ("Entity Gap", "Content Gap"),
    )


def _professional_task(diagnostic: dict[str, Any]) -> dict[str, Any]:
    return _task(
        "P2",
        "专业内容建设任务",
        "增强 AI 对企业专业性的判断。",
        ["行业知识", "技术说明", "产品应用", "常见问题", "用户决策信息"],
        "专业内容方向",
        diagnostic,
        ("Content Gap", "Query Gap"),
    )


def _trust_task(diagnostic: dict[str, Any]) -> dict[str, Any]:
    return _task(
        "P2",
        "信任信息增强任务",
        "提升 AI 推荐企业时的可信度。",
        ["企业资质", "生产能力", "项目经验", "客户案例", "行业证明"],
        "企业信任资料库",
        diagnostic,
        ("Evidence Gap", "Authority Gap", "Trust Gap", "Experience Gap"),
    )


def _search_readiness_task(diagnostic: dict[str, Any]) -> dict[str, Any]:
    return _task(
        "P3",
        "AI搜索适配准备任务",
        "为下一阶段 GEO 优化提供基础输入。",
        ["用户关注场景", "企业服务场景", "用户问题方向", "行业需求方向"],
        "GEO优化基础数据",
        diagnostic,
        ("Query Gap", "Content Gap"),
    )


def _task(
    priority: str,
    title: str,
    goal: str,
    needs: list[str],
    output: str,
    diagnostic: dict[str, Any],
    gap_types: tuple[str, ...],
) -> dict[str, Any]:
    gaps = [
        item
        for item in ((diagnostic.get("gaps") or {}).get("gaps") or [])
        if str(item.get("type")) in gap_types
    ]
    basis = [str(item.get("reason")) for item in gaps[:3] if item.get("reason")]
    if not _real_observations(diagnostic):
        basis.insert(0, f"{UNKNOWN} 当前没有真实 AI 观察，以下任务依据仅来自企业资料与诊断缺口。")
    return {
        "id": TASK_IDS.get(title, "task_unknown"),
        "priority": priority,
        "title": title,
        "goal": goal,
        "needs": needs,
        "output": output,
        "basis": basis or ["当前诊断未记录该模块的单独 Gap；作为下一阶段能力交接项保留。"],
    }


def _real_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    observations = (diagnostic.get("ai_cognition") or {}).get("observations") or []
    return [
        item
        for item in observations
        if str(item.get("status") or item.get("observation_mode") or "").lower() in REAL_MODES
    ]


def _rate(value: Any) -> str:
    return UNKNOWN if value is None else f"{value}%"


def _score(value: Any) -> str:
    return UNKNOWN if value is None else f"{value}/100"


def _text(value: Any) -> str:
    return str(value or UNKNOWN)
