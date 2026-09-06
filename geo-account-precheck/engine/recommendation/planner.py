"""Recommendation planner: converts gaps and opportunities into executable tasks."""

from __future__ import annotations

from typing import Any

from ..models.recommendation import RecommendationAction

CASE_MATERIALS = [
    "客户行业",
    "客户名称",
    "项目名称",
    "项目地点",
    "原始问题",
    "解决方案",
    "产品",
    "项目结果",
    "项目照片",
    "验收资料",
]

TITLE_TO_GAP = {
    "补齐企业基础实体资料": "Entity Gap",
    "为高频推荐 Query 补齐内容": "Query Gap",
    "建立可核验证据包": "Evidence Gap",
    "补充真实客户案例": "Experience Gap",
    "补充第三方权威证明": "Authority Gap",
    "按场景补齐画像内容": "Content Gap",
    "提升 AI 引用/采信率": "Citation Gap",
    "提升信任基础与来源核验": "Trust Gap",
    "修复全网 NAP 冲突": "Local/NAP Gap",
    "缩小与竞品的可比差距": "Competitor Gap",
}

ACTION_SPECS: dict[str, dict[str, Any]] = {
    "Entity Gap": {
        "task": "补齐公司基础实体资料",
        "action": "按 EntityProfile 字段整理企业全称、业务、产品、服务、客群、地域、创始人、专家、资质、官网和联系方式，逐条标来源。",
        "materials": ["工商注册信息", "官网", "产品目录", "资质证书", "创始人介绍"],
        "verification": "资料补齐后重新运行诊断并对照 Entity Score。",
        "heuristics": ["实体缺失时不能把 INFERENCE 当 FACT 写入画像。"],
    },
    "Query Gap": {
        "task": "为高频推荐 Query 补齐内容",
        "action": "针对未覆盖 Query 逐一创建证据型内容，优先推荐型、决策型和地域型 Query。",
        "materials": ["真实产品参数", "客户案例", "场景实拍", "FAQ"],
        "verification": "发布成功 20 篇后间隔 7-15 天复测；再次发布后间隔 7 天更新报表。",
        "heuristics": ["发布数量是 Operational Heuristic，不是 Guaranteed Rule。"],
    },
    "Evidence Gap": {
        "task": "建立可核验证据包",
        "action": "为每项声明补齐来源、日期、来源类型、是否核验；优先第三方/媒体/政府来源。",
        "materials": ["参数检测报告", "验收单", "项目照片", "第三方测评", "媒体原文链接"],
        "verification": "重新运行 EvidenceVerifier，目标全部条目有来源、日期并可核验。",
        "heuristics": ["Evidence 缺失是豆包不推荐的第一高频原因。"],
    },
    "Experience Gap": {
        "task": "补充真实客户案例",
        "action": "从真实交付项目中整理 3 个客户案例，写清客户、问题、方案、产品和结果。",
        "materials": CASE_MATERIALS,
        "verification": "案例上线后按 20 篇/7-15 天规则复测 Experience 与推荐率。",
        "heuristics": ["只喊深耕多年不算 Experience，必须有落地项目和场景。"],
    },
    "Authority Gap": {
        "task": "补充第三方权威证明",
        "action": "收集官方资质、认证、专利、专家署名和第三方媒体覆盖，并保留可核验链接。",
        "materials": ["资质证书", "专利号", "检测报告", "媒体报道链接", "专家履历"],
        "verification": "复测 EEAT Authoritativeness 和推荐问答中的提及原因。",
        "heuristics": ["资质齐全不等于会被推荐；证据和准确性仍要达标。"],
    },
    "Content Gap": {
        "task": "按画像九大板块优化内容",
        "action": "对九大画像模块做 Evidence Coverage 判断，只优化有证据缺口且与 Query 相关的模块。",
        "materials": ["九大板块现有内容", "证据文件", "高频 Query 列表"],
        "verification": "内容发布后复测各模块对应 Query 的覆盖率。",
        "heuristics": ["不要为了内容量发布没有证据支持的宣传话术。"],
    },
    "Citation Gap": {
        "task": "提升 AI 引用/采信率",
        "action": "用第三方商业媒体+搜索&问答场景词提量投喂，并将可核验信息放在能被引用的句式里。",
        "materials": ["可引用事实", "来源链接", "发布记录"],
        "verification": "复测记录 AI 是否直接引用企业来源及引用理由。",
        "heuristics": ["文章数量不等于 AI 认知，引用率才是可观察指标。"],
    },
    "Trust Gap": {
        "task": "提升信任基础与来源核验",
        "action": "核验每条 Evidence、统一全网 NAP，并移除冲突或过期信息。",
        "materials": ["Evidence 清单", "平台 NAP 截图", "核验记录"],
        "verification": "核验后 7 天复测 AI 对电话/官网和企业的描述。",
        "heuristics": ["EEAT 不足时先补专家、资质、品牌名气、媒体报道。"],
    },
    "Local/NAP Gap": {
        "task": "修复全网 NAP 冲突",
        "action": "逐项核对知识库公司信息、画像设置、图片、Agent 官网、AI 官网、企查查和地图，确保电话/官网一致。",
        "materials": ["后台各配置截图", "企查查信息", "地图 APP 信息"],
        "verification": "统一后 7 天在豆包等平台测试电话和官网露出。",
        "heuristics": ["NAP 不一致会让 AI 无法安全露出联系方式。"],
    },
    "Competitor Gap": {
        "task": "收集竞品可比数据",
        "action": "确认 3-5 个竞品，记录 AI 观察中的推荐率、提及率、引用率和权威维度，找出客户缺席的 Query。",
        "materials": ["竞品清单", "AI 问答记录", "竞品官网/资质/媒体"],
        "verification": "建立竞品基线后，每轮优化结束复测同一批 Query。",
        "heuristics": ["竞品状态必须 candidate/confirmed，不能凭名称自动当成事实。"],
    },
}


class RecommendationPlanner:
    def plan(
        self,
        gaps: list[dict[str, Any]],
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        actions: list[RecommendationAction] = []
        for opportunity in opportunities:
            gap_type = TITLE_TO_GAP.get(opportunity["title"], opportunity["title"])
            gap = next((item for item in gaps if item["type"] == gap_type), {"type": gap_type, "reason": "GEO 缺口", "evidence": [], "affected_queries": []})
            spec = ACTION_SPECS.get(gap_type, ACTION_SPECS.get("Evidence Gap"))
            action = RecommendationAction(
                task=opportunity["title"],
                priority=opportunity["priority"],
                problem=str(gap.get("reason") or "GEO 缺口"),
                why=opportunity.get("reason") or "由机会评分推导。",
                evidence=list(gap.get("evidence") or []),
                impact=list(gap.get("affected_queries") or []),
                action=spec["action"],
                required_materials=spec["materials"],
                verification=spec["verification"],
                source_doc_heuristics=spec["heuristics"],
            )
            actions.append(action)
        return {
            "status": "COMPUTED",
            "count": len(actions),
            "actions": [action.to_dict() for action in actions],
        }
