"""Render the compact enterprise AI growth diagnosis report."""

from __future__ import annotations

from typing import Any


UNKNOWN = "【需企业提供真实佐证】"


def render_growth_report(diagnostic: dict[str, Any]) -> str:
    company = diagnostic.get("company") or {}
    visibility = diagnostic.get("ai_visibility") or {}
    eeat = diagnostic.get("eeat_score") or {}
    score = diagnostic.get("growth_score") or {}
    gaps = diagnostic.get("geo_gap") or {}
    prescription = diagnostic.get("growth_prescription") or {}
    position = (diagnostic.get("diagnosis_summary") or {}).get("company_position") or UNKNOWN
    lines = [
        "# 企业AI增长诊断报告",
        "",
        f"企业：{company.get('name') or UNKNOWN}",
        "",
        "## 1 企业AI认知总览",
        "",
        f"- GEO Score：{_score(score.get('total'))}",
        f"- AI认知阶段：{visibility.get('visibility_stage') or UNKNOWN}",
        f"- 当前状态：{prescription.get('current_status') or UNKNOWN}",
        "",
        "## 2 企业定位诊断",
        "",
        f"- 企业是谁：{position}",
        f"- 卖什么：{_company_values(company, 'products')}",
        f"- 服务谁：{_company_values(company, 'customers')}",
        f"- 解决什么：{company.get('business') or UNKNOWN}",
        f"- 为什么选择：{_why_choose(diagnostic)}",
        "",
        "## 3 AI可见度分析",
        "",
        "| 指标 | 结果 |",
        "|---|---|",
        f"| 品牌认知 | {_score(visibility.get('brand_recognition'))} |",
        f"| 业务理解 | {_score(visibility.get('business_understanding'))} |",
        f"| 信任程度 | {_score(visibility.get('trust_level'))} |",
        f"| 推荐概率 | {_score(visibility.get('recommend_probability'))} |",
        "",
        "模拟问题：行业推荐、产品选择、方案咨询、供应商选择。",
        f"真实观察：{_observation_count(diagnostic)} 条；没有真实观察的场景不计入 AI 认知评分。",
        "",
        "## 4 用户需求场景",
        "",
        "用户决策路径：发现问题 → 理解企业 → 判断专业性 → 验证信任 → 形成推荐。",
        "",
        "## 5 GEO竞争分析",
        "",
        _competition(diagnostic),
        "",
        "## 6 EEAT信任评分",
        "",
        "| 维度 | 分数 |",
        "|---|---:|",
        f"| Expertise | {_score(eeat.get('expertise'), suffix='/25')} |",
        f"| Experience | {_score(eeat.get('experience'), suffix='/25')} |",
        f"| Authority | {_score(eeat.get('authority'), suffix='/25')} |",
        f"| Trust | {_score(eeat.get('trust'), suffix='/25')} |",
        f"| Total | {_score(eeat.get('total'))} |",
        "",
        "## 7 GEO缺口地图",
        "",
        "| 问题 | 原因 | 影响 | 优先级 |",
        "|---|---|---|---|",
    ]
    for item in (gaps.get("gaps") or [])[:12]:
        lines.append(
            f"| {item.get('problem') or UNKNOWN} | {item.get('reason') or UNKNOWN} | "
            f"{item.get('impact') or UNKNOWN} | {item.get('priority') or UNKNOWN} |"
        )
    if not gaps.get("gaps"):
        lines.append(f"| {UNKNOWN} | {UNKNOWN} | {UNKNOWN} | P0 |")
    lines.extend(["", "## 8 GEO增长处方", ""])
    for item in prescription.get("priority_actions") or []:
        lines.append(f"- {item.get('priority') or UNKNOWN}｜{item.get('task') or UNKNOWN}：{item.get('action') or UNKNOWN}")
    lines.extend(
        [
            "",
            f"30天：{prescription.get('30_days') or UNKNOWN}",
            f"60天：{prescription.get('60_days') or UNKNOWN}",
            f"90天：{prescription.get('90_days') or UNKNOWN}",
            "",
            "> GEO-BD 输出诊断和处方；具体内容生产与长期运营由后续 GEO Skill 执行。",
            "",
        ]
    )
    return "\n".join(lines)


def render_positioning_report(diagnostic: dict[str, Any]) -> str:
    company = diagnostic.get("company") or {}
    position = (diagnostic.get("diagnosis_summary") or {}).get("company_position") or UNKNOWN
    return "\n".join(
        [
            "# 企业定位分析",
            "",
            f"- 企业是谁：{position}",
            f"- 卖什么：{_company_values(company, 'products')}",
            f"- 服务谁：{_company_values(company, 'customers')}",
            f"- 解决什么：{company.get('business') or UNKNOWN}",
            f"- 为什么选择：{_why_choose(diagnostic)}",
            "",
        ]
    )


def render_gap_map(diagnostic: dict[str, Any]) -> str:
    lines = ["# GEO缺口地图", "", "| 问题 | 原因 | 影响 | 优先级 |", "|---|---|---|---|"]
    for item in ((diagnostic.get("geo_gap") or {}).get("gaps") or []):
        lines.append(
            f"| {item.get('problem') or UNKNOWN} | {item.get('reason') or UNKNOWN} | "
            f"{item.get('impact') or UNKNOWN} | {item.get('priority') or UNKNOWN} |"
        )
    return "\n".join(lines) + "\n"


def render_eeat_report(diagnostic: dict[str, Any]) -> str:
    score = diagnostic.get("eeat_score") or {}
    lines = ["# EEAT评分报告", "", "| 维度 | 分数 |", "|---|---:|"]
    for key, label in (("expertise", "Expertise"), ("experience", "Experience"), ("authority", "Authority"), ("trust", "Trust")):
        lines.append(f"| {label} | {_score(score.get(key), suffix='/25')} |")
    lines.extend([f"| Total | {_score(score.get('total'))} |", "", "缺失资产："])
    lines.extend(f"- {item}" for item in score.get("missing_assets") or [UNKNOWN])
    return "\n".join(lines) + "\n"


def render_competition_report(diagnostic: dict[str, Any]) -> str:
    return "# 竞争分析\n\n" + _competition(diagnostic) + "\n"


def render_growth_prescription(diagnostic: dict[str, Any]) -> str:
    prescription = diagnostic.get("growth_prescription") or {}
    lines = ["# GEO优化处方", "", f"当前状态：{prescription.get('current_status') or UNKNOWN}", ""]
    for item in prescription.get("priority_actions") or []:
        lines.extend([f"## {item.get('priority') or UNKNOWN}｜{item.get('task') or UNKNOWN}", "", str(item.get("action") or UNKNOWN), ""])
    lines.extend([
        f"30天：{prescription.get('30_days') or UNKNOWN}",
        f"60天：{prescription.get('60_days') or UNKNOWN}",
        f"90天：{prescription.get('90_days') or UNKNOWN}",
        "",
    ])
    return "\n".join(lines)


def _company_values(company: dict[str, Any], key: str) -> str:
    value = company.get(key) or ((company.get("raw") or {}).get(key))
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or UNKNOWN
    return str(value or UNKNOWN)


def _why_choose(diagnostic: dict[str, Any]) -> str:
    evidence = (diagnostic.get("evidence_graph") or {}).get("items") or []
    return "已有企业资料和 Evidence 支撑；具体差异化优势需企业提供真实佐证。" if evidence else UNKNOWN


def _competition(diagnostic: dict[str, Any]) -> str:
    competitors = (diagnostic.get("competitors") or {}).get("competitors") or []
    if not competitors:
        return UNKNOWN + " 当前没有已确认竞品对比资料。"
    names = "、".join(str(item.get("name")) for item in competitors if item.get("name"))
    strengths = []
    for item in competitors:
        if item.get("recommendation_rate") is not None:
            strengths.append(f"{item.get('name') or UNKNOWN} 推荐率 {item.get('recommendation_rate')}%")
    detail = "；".join(strengths)
    return f"已确认竞品：{names or UNKNOWN}。竞品 AI 认知优势：{detail or UNKNOWN}。现有分析仅表示诊断差距，不代表市场排名。"


def _observation_count(diagnostic: dict[str, Any]) -> int:
    return len(
        [
            item
            for item in (diagnostic.get("ai_cognition") or {}).get("observations") or []
            if str(item.get("status") or item.get("observation_mode") or "").lower() in {"observed", "provided"}
        ]
    )


def _score(value: Any, suffix: str = "/100") -> str:
    return UNKNOWN if value is None else f"{value}{suffix}"
