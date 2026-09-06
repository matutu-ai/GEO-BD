"""Render a DiagnosticResult dict as the V2 GEO Diagnostic Markdown report."""

from __future__ import annotations

from typing import Any, Iterable


def render_markdown(result: dict[str, Any]) -> str:
    meta = result.get("meta") or {}
    engine_label = f"{_text(meta.get('engine'), 'GEO Diagnostic Engine')} {_text(meta.get('version'), '')}".strip()
    lines: list[str] = [
        "# GEO Diagnostic Report",
        "",
        f"- Engine：{engine_label}",
        f"- 生成时间：{_text(meta.get('generated_at'))}",
        f"- Research Mode：{_text(meta.get('research_mode'))}",
        f"- 说明：{_text(meta.get('diagnostic_note'))}",
        "",
        "## 01 Executive Summary",
        "",
    ]
    scores = result.get("scores") or {}
    lines.extend(
        [
            f"当前 GEO 诊断状态：{_score_text(scores.get('geo_score'))}",
            "",
            "核心问题：",
        ]
    )
    problems = _critical_problems(result)
    if problems:
        for index, item in enumerate(problems, start=1):
            lines.append(f"{index}. {item}")
    else:
        lines.append("1. 尚无足够数据判断核心问题；先补齐企业资料和真实 AI 观察。")
    lines.extend(["", "最大机会："])
    opportunities = (result.get("opportunities") or {}).get("opportunities") or []
    for opportunity in opportunities[:3]:
        lines.append(
            f"- {_text(opportunity.get('title'))}（{_text(opportunity.get('priority'))}，"
            f"{_score_text(opportunity.get('score'))}）"
        )
    if not opportunities:
        lines.append("- 数据不足，无法排序机会。")

    actions = (result.get("recommendations") or {}).get("actions") or []
    p0_actions = [action for action in actions if str(action.get("priority")) == "P0"]
    lines.extend(["", "P0："])
    if p0_actions:
        for index, action in enumerate(p0_actions[:3], start=1):
            lines.append(f"{index}. {_text(action.get('task'))}")
    elif actions:
        top = actions[0]
        lines.append(f"暂无独立 P0；最高优先级为 {_text(top.get('priority'))}：{_text(top.get('task'))}。")
    else:
        lines.append("1. 数据不足，先补齐企业资料与真实 AI 观察。")
    lines.extend(["", "需要客户补充：", *(_required_materials(result) or ["1. 先补齐企业基础实体、Evidence 与真实 AI 观察资料。"])])
    lines.extend(
        [
            "",
            "建议7天：完成 P0 资料核验、NAP 统一和真实 AI 基线观察。",
            "",
            "建议30天：按 P0/P1 动作发布证据型内容，再以同一批 Query 复测并比较指标。",
            "",
        ]
    )
    _entity_section(lines, result.get("company") or {}, result.get("entity") or {})
    _cognition_section(lines, result.get("ai_cognition") or {})
    _query_section(lines, result.get("query_matrix") or {})
    _competitor_section(lines, result.get("competitors") or {})
    _evidence_section(lines, result.get("evidence_graph") or {})
    _eeaap_section(lines, result.get("eeaap") or {})
    _eeat_section(lines, result.get("eeat") or {})
    _scenario_section(lines, result.get("scenarios") or {})
    _keyword_section(lines, result.get("keywords") or {}, result.get("scenarios") or {})
    _ai_test_section(lines, result.get("ai_tests") or {}, result.get("citations") or {})
    _nap_section(lines, result.get("nap") or {}, result.get("scores") or {})
    _gap_section(lines, result.get("gaps") or {})
    _opportunity_section(lines, opportunities)
    _action_section(lines, result.get("recommendations") or {})
    _next_test_section(lines, result)
    _validation_section(lines, result.get("validation") or {})
    _quality_section(lines, result.get("data_quality") or {})
    _unknown_section(lines, result)
    return "\n".join(lines).rstrip() + "\n"


def _entity_section(lines: list[str], company: dict[str, Any], entity: dict[str, Any]) -> None:
    lines.extend(["## 02 Company Entity", "", "结构化企业实体（来源状态均保留）：", "", "| 字段 | 值 | 状态 | 来源 | 可信度 |", "|---|---|---|---|---|"])
    fields = entity.get("fields") or {}
    labels = {
        "name": "企业名称",
        "aliases": "企业别名",
        "brands": "品牌名",
        "business": "主营业务",
        "products": "产品",
        "services": "服务",
        "customers": "客户",
        "cases": "客户案例",
        "locations": "地域",
        "founders": "创始人",
        "experts": "专家",
        "certificates": "资质",
        "patents": "专利",
        "media": "媒体",
        "website": "官网",
        "contacts": "联系方式",
        "address": "地址",
        "phone": "电话",
        "social_accounts": "社交媒体",
        "reviews": "客户评价",
        "negative_information": "负面信息",
    }
    for key, values in fields.items():
        display = [item.get("value") or "UNKNOWN" for item in values if item.get("status") != "UNKNOWN"]
        display = display or ["UNKNOWN"]
        sources = [item.get("source") or "未知来源" for item in values if item.get("value")]
        confidences = [item.get("confidence") or 0 for item in values if item.get("value")]
        lines.append(
            f"| {labels.get(key, key)} | {_join(display)} | "
            f"{_join([item.get('status') for item in values]) or 'UNKNOWN'} | "
            f"{_join(sources) or '未知来源'} | {_join([str(item) for item in confidences]) or '0'} |"
        )
    lines.append("")


def _cognition_section(lines: list[str], cognition: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 03 AI Cognition",
            "",
            f"- 观察模式：{_text(cognition.get('observation_mode'), 'UNKNOWN')}",
            f"- 状态：{_text(cognition.get('status'), 'UNKNOWN')}",
            f"- AI 认知评分：{_score_text(cognition.get('score'))}",
            f"- 说明：{_text(cognition.get('basis'))}",
            "",
            "| Query | 类型 | 被提及 | 被推荐 | 被正确描述 | 被引用 | 位置 | 模式 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    observations = cognition.get("observations") or []
    for item in observations:
        lines.append(
            f"| {_text(item.get('query'))} | {_text(item.get('query_type'))} | "
            f"{_yes_no(item.get('company_mentioned'))} | {_yes_no(item.get('company_recommended'))} | "
            f"{_yes_no(item.get('company_correctly_described'))} | {_yes_no(item.get('company_cited'))} | "
            f"{_text(item.get('position'), '-')} | {_text(item.get('observation_mode'), 'unknown')} |"
        )
    if not observations:
        lines.append("| 无真实观察 | - | - | - | - | - | - | UNKNOWN |")
    lines.append("")


def _query_section(lines: list[str], matrix: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 04 Query Intelligence",
            "",
            f"- Query 总数：{matrix.get('total', 0)}",
            f"- Matrix 状态：{_text(matrix.get('status'), 'UNKNOWN')}",
            "",
        ]
    )
    coverage = matrix.get("coverage") or {}
    if coverage.get("status") == "UNKNOWN":
        lines.append(f"- Query Coverage：{_text(coverage.get('status'))}；{_text(coverage.get('basis'))}")
    else:
        lines.extend(
            [
                "Coverage：",
                "",
                "| 指标 | 数值 |",
                "|---|---|",
                f"| 提及率 | {_score_text(coverage.get('mention_rate'))} |",
                f"| 推荐率 | {_score_text(coverage.get('recommendation_rate'))} |",
                f"| 描述准确率 | {_score_text(coverage.get('description_accuracy'))} |",
                f"| 引用率 | {_score_text(coverage.get('citation_rate'))} |",
                f"| 场景覆盖 | {_score_text(coverage.get('scenario_coverage'))} |",
                f"| Coverage Score | {_score_text(coverage.get('score'))} |",
                f"| 说明 | {_text(coverage.get('basis'))} |",
                "",
            ]
        )
    lines.extend(["Query 列表（按意图分组）：", ""])
    queries = matrix.get("queries") or []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for query in queries:
        intent = str(query.get("intent") or "unknown")
        grouped.setdefault(intent, []).append(query)
    if not grouped:
        lines.append("- UNKNOWN：没有可诊断的真实 Query。")
    for intent, items in grouped.items():
        lines.append(f"- {intent}（{len(items)}）")
        for item in items[:8]:
            lines.append(f"  - {_text(item.get('query'))}")
        if len(items) > 8:
            lines.append(f"  - 另有 {len(items) - 8} 条同类型 Query")
    lines.append("")


def _competitor_section(lines: list[str], competitor: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 05 Competitor Intelligence",
            "",
            f"- 状态：{_text(competitor.get('status'), 'UNKNOWN')}",
            f"- Competitor Gap Score：{_score_text(competitor.get('score'))}",
            f"- 说明：{_text(competitor.get('basis'))}",
            "",
            "| 竞品 | 状态 | 提及率 | 推荐率 | Evidence | Authority | 引用率 |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in competitor.get("competitors") or []:
        lines.append(
            f"| {_text(item.get('name'))} | {_text(item.get('status'))} | "
            f"{_score_text(item.get('mention_rate'))} | {_score_text(item.get('recommendation_rate'))} | "
            f"{_score_text(item.get('evidence_count'))} | {_score_text(item.get('authority_score'))} | "
            f"{_score_text(item.get('citation_rate'))} |"
        )
    if not (competitor.get("competitors") or []):
        lines.append("| UNKNOWN | - | - | - | - | - | - |")
    lines.extend(["", "| 维度 | 客户 | 竞品 | 差距 | 状态 |", "|---|---|---|---|---|"])
    for gap in competitor.get("gap_matrix") or []:
        lines.append(
            f"| {_text(gap.get('dimension'))} | {_score_text(gap.get('client_score'))} | "
            f"{_score_text(gap.get('competitor_score'))} | {_score_text(gap.get('gap'))} | "
            f"{_text(gap.get('status'))} |"
        )
    if not (competitor.get("gap_matrix") or []):
        lines.append("| UNKNOWN | - | - | - | UNKNOWN |")
    lines.append("")


def _evidence_section(lines: list[str], graph: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 06 Evidence Graph",
            "",
            f"- 节点：{len(graph.get('nodes') or [])}；边：{len(graph.get('edges') or [])}；Evidence：{len(graph.get('items') or [])}",
            "",
        ]
    )
    edges = graph.get("edges") or []
    if edges:
        lines.extend(["Graph 边：", ""])
        for edge in edges[:30]:
            lines.append(f"- {_text(edge.get('source'))} -> {_text(edge.get('relation'))} -> {_text(edge.get('target'))}")
        if len(edges) > 30:
            lines.append(f"- 另有 {len(edges) - 30} 条边")
        lines.append("")
    lines.extend(["| Evidence ID | 声明 | 状态 | 来源类型 | 来源 | 日期 | 核验 | 可信度 |", "|---|---|---|---|---|---|---|---|"])
    for item in graph.get("items") or []:
        lines.append(
            f"| {_text(item.get('id'))} | {_truncate(_text(item.get('claim')), 60)} | {_text(item.get('status'))} | "
            f"{_text(item.get('source_type'))} | {_text(item.get('source'))} | {_text(item.get('date'), '-')} | "
            f"{'是' if item.get('verified') else '否'} | {_score_text(item.get('confidence'))} |"
        )
    if not (graph.get("items") or []):
        lines.append("| - | UNKNOWN | UNKNOWN | - | - | - | - | 0 |")
    lines.append("")


def _eeaap_section(lines: list[str], eeaap: dict[str, Any]) -> None:
    lines.extend(["## 07 EEAAP", "", "| 维度 | 分数 |", "|---|---|"])
    for key, label in (
        ("experience", "Experience 经验"),
        ("evidence", "Evidence 证据"),
        ("authoritativeness", "Authoritativeness 权威性"),
        ("accuracy", "Accuracy 准确性"),
        ("perspective", "Perspective 视角"),
        ("overall", "Overall 总分"),
    ):
        lines.append(f"| {label} | {_score_text(eeaap.get(key))} |")
    lines.extend(["", "Gaps："])
    for gap in eeaap.get("gaps") or []:
        lines.append(f"- {gap}")
    if not (eeaap.get("gaps") or []):
        lines.append("- 暂无")
    lines.append("")


def _eeat_section(lines: list[str], eeat: dict[str, Any]) -> None:
    lines.extend(["## 08 EEAT", "", "| 维度 | 分数 |", "|---|---|"])
    for key, label in (
        ("experience", "Experience"),
        ("expertise", "Expertise"),
        ("authoritativeness", "Authoritativeness"),
        ("trustworthiness", "Trustworthiness"),
        ("overall", "Overall 总分"),
    ):
        lines.append(f"| {label} | {_score_text(eeat.get(key))} |")
    lines.extend(["", "Gaps："])
    for gap in eeat.get("gaps") or []:
        lines.append(f"- {gap}")
    if not (eeat.get("gaps") or []):
        lines.append("- 暂无")
    lines.extend(["", f"EEAT 与 EEAAP 的差异：{_text(eeat.get('difference_from_eeaap'))}", ""])


def _scenario_section(lines: list[str], scenarios: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 09 Scenario Coverage",
            "",
            f"- Scenario 状态：{_text(scenarios.get('scenario_status'), 'UNKNOWN')}",
            f"- Scenario Coverage：{_score_text(scenarios.get('scenario_coverage'))}",
            f"- Scenario Score：{_score_text(scenarios.get('scenario_coverage_score'))}",
            f"- 说明：{_text(scenarios.get('basis'))}",
            "",
            "| 场景 | 目标 Query | 已覆盖 | 覆盖率 | 状态 |",
            "|---|---|---|---|---|",
        ]
    )
    scenario_items = scenarios.get("scenarios") or []
    if scenario_items:
        for item in scenario_items:
            lines.append(
                f"| {_text(item.get('label'))} | {item.get('target_count', 0)} | {item.get('covered_count', 0)} | "
                f"{_score_text(item.get('coverage'))} | {_text(item.get('status'))} |"
            )
    else:
        lines.append("| UNKNOWN | - | - | - | UNKNOWN |")
    lines.append("")


def _keyword_section(lines: list[str], keywords: dict[str, Any], scenarios: dict[str, Any]) -> None:
    keyword_list = scenarios.get("keywords") or keywords.get("keywords") or []
    keyword_coverage = keywords.get("coverage")
    if keyword_coverage is None:
        keyword_coverage = keywords.get("keyword_coverage") or scenarios.get("keyword_coverage")
    score_value = scenarios.get("keyword_coverage_score")
    if score_value is None:
        score_value = keywords.get("keyword_coverage_score")
    lines.extend(
        [
            "## 10 Keyword Coverage",
            "",
            f"- Keyword 状态：{_text(keywords.get('status'), 'UNKNOWN')}",
            f"- Keyword Coverage：{_score_text(keyword_coverage)}",
            f"- Keyword Score：{_score_text(score_value)}",
            f"- 说明：{_text(keywords.get('basis') or scenarios.get('basis'))}",
            "",
            "| 关键词 | 类型 | 意图 | 场景 | 优先级 |",
            "|---|---|---|---|---|",
        ]
    )
    if keyword_list:
        for item in keyword_list[:40]:
            lines.append(
                f"| {_text(item.get('keyword'))} | {_text(item.get('type'))} | {_text(item.get('intent'))} | "
                f"{_text(item.get('scenario'))} | {_text(item.get('priority'), '-')} |"
            )
        if len(keyword_list) > 40:
            lines.append(f"| 另有 {len(keyword_list) - 40} 条关键词 | - | - | - | - |")
    else:
        lines.append("| UNKNOWN | - | - | - | - |")
    lines.append("")


def _ai_test_section(lines: list[str], ai_tests: dict[str, Any], citations: dict[str, Any]) -> None:
    block = ai_tests if ai_tests.get("status") else citations
    lines.extend(
        [
            "## 11 AI Test",
            "",
            f"- AI Test 状态：{_text(block.get('status'), 'NOT_RUN')}",
            f"- 测试样本：{_text(block.get('total'), '0')}",
            f"- Mention Rate：{_score_text(block.get('mention_rate'))}",
            f"- Recommendation Rate：{_score_text(block.get('recommendation_rate'))}",
            f"- Citation Rate：{_score_text(block.get('citation_rate'))}",
            f"- Average Position：{_score_text(block.get('average_position'))}",
            f"- 说明：{_text(block.get('basis'))}",
            "",
        ]
    )
    results = block.get("results") or []
    if results:
        lines.extend(
            [
                "| Query | 平台 | Mention | Recommendation | Citation | Position | 竞品 |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for item in results:
            lines.append(
                f"| {_truncate(_text(item.get('query')), 45)} | {_text(item.get('platform'), '-')} | "
                f"{_yes_no(item.get('company_mentioned'))} | {_yes_no(item.get('company_recommended'))} | "
                f"{_yes_no(item.get('company_cited') or item.get('citation_found'))} | "
                f"{_text(item.get('position'), '-')} | {_join(item.get('competitors_mentioned')) or '-'} |"
            )
        lines.append("")
    if block.get("status") == "NOT_RUN":
        lines.extend(["无真实 AI 测试结果时不计算任何数字；先导入真实回答后再查看指标。", ""])


def _nap_section(lines: list[str], nap: dict[str, Any], scores: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 12 NAP / Trust",
            "",
            f"- NAP 状态：{_text(nap.get('status'))}",
            f"- NAP 一致性：{_text('一致' if nap.get('consistent') else '不一致' if nap.get('consistent') is False else 'UNKNOWN')}",
            f"- NAP Score：{_score_text(scores.get('nap_score'))}",
            f"- 说明：{_text(nap.get('basis'))}",
            "",
            "| 字段 | 当前值 |",
            "|---|---|",
        ]
    )
    fields = nap.get("fields") or {}
    for key, label in (("name", "Name 企业名"), ("website", "官网"), ("phone", "Phone 电话"), ("address", "Address 地址")):
        lines.append(f"| {label} | {_text(fields.get(key), '-')} |")
    conflicts = nap.get("conflicts") or []
    if conflicts:
        lines.extend(["", "冲突："] + [f"- {item}" for item in conflicts])
    lines.append("")


def _gap_section(lines: list[str], gaps: dict[str, Any]) -> None:
    lines.extend(["## 13 GEO Gap", "", "| Gap | 严重度 | 缺口分数 | 原因 |", "|---|---|---|---|"])
    for gap in gaps.get("gaps") or []:
        lines.append(
            f"| {_text(gap.get('type'))} | {_text(gap.get('severity'))} | {_score_text(gap.get('score'))} | "
            f"{_truncate(_text(gap.get('reason')), 70)} |"
        )
    if not (gaps.get("gaps") or []):
        lines.append("| - | UNKNOWN | - | 无数据 |")
    lines.append("")


def _opportunity_section(lines: list[str], opportunities: list[dict[str, Any]]) -> None:
    lines.extend(
        [
            "## 14 GEO Opportunity",
            "",
            "| 机会 | 分数 | 优先级 | Business | AI Demand | 竞品差距 | 证据可得 | 可行性 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in opportunities:
        lines.append(
            f"| {_text(item.get('title'))} | {_score_text(item.get('score'))} | {_text(item.get('priority'))} | "
            f"{_score_text(item.get('business_value'))} | {_score_text(item.get('ai_demand'))} | "
            f"{_score_text(item.get('competitor_gap'))} | {_score_text(item.get('evidence_availability'))} | "
            f"{_score_text(item.get('feasibility'))} |"
        )
    if not opportunities:
        lines.append("| - | UNKNOWN | - | - | - | - | - | - |")
    lines.append("")


def _action_section(lines: list[str], recommendations: dict[str, Any]) -> None:
    actions = recommendations.get("actions") or []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for action in actions:
        grouped.setdefault(str(action.get("priority") or "P2"), []).append(action)
    lines.append("## 15 P0/P1/P2/P3 Action Plan")
    if not actions:
        lines.extend(["", "- 暂无动作，先补齐数据后再生成。", ""])
        return
    for priority in ("P0", "P1", "P2", "P3"):
        items = grouped.get(priority) or []
        if not items:
            continue
        lines.extend(["", f"### {priority}", ""])
        for action in items:
            lines.extend(
                [
                    f"**{_text(action.get('task'))}**",
                    f"- 问题：{_text(action.get('problem'))}",
                    f"- 为什么：{_text(action.get('why'))}",
                    f"- 影响：{_join(action.get('impact')) or '相关 Query/评分维度'}",
                    f"- 动作：{_text(action.get('action'))}",
                    f"- 所需资料：{_join(action.get('required_materials'))}",
                    f"- 验证：{_text(action.get('verification'))}",
                    "",
                ]
            )
    lines.append("")


def _next_test_section(lines: list[str], result: dict[str, Any]) -> None:
    ai_tests = result.get("ai_tests") or {}
    citations = result.get("citations") or {}
    matrix = result.get("query_matrix") or {}
    queries = matrix.get("queries") or []
    observations = (result.get("ai_cognition") or {}).get("observations") or []
    untested = [
        str(query.get("query"))
        for query in queries
        if str(query.get("query")) not in {str(item.get("query")) for item in observations}
    ]
    lines.extend(
        [
            "## 16 Next Test",
            "",
            "下一轮必须用同一批 Query 做真实 AI 测试并逐条记录：",
        ]
    )
    if observations:
        lines.extend(
            [
                f"- 已观察 {len(observations)} 条；请补测以下目标 Query：",
                *(f"  - {item}" for item in untested[:12]),
            ]
        )
        if not untested:
            lines.extend(["- 本批 Query 已全部有观察记录；复测时保持 Query 不变。", ""])
    else:
        lines.extend(
            [
                "- 尚无真实观察记录；先执行 Baseline：",
                *(f"  - {item}" for item in (queries[:12] or ["企业品牌/产品/场景/推荐 Query"])),
                "",
            ]
        )
    lines.extend(
        [
            f"- 当前 AI Test：{_text(ai_tests.get('status') or citations.get('status'), 'NOT_RUN')}",
            "- 记录字段：Query、平台、是否 Mention、是否 Recommendation、是否 Citation、Position、竞品与回答原文。",
            "- 复测节奏：发布证据型内容成功 20 篇后间隔 7-15 天；随后每次间隔 7 天。",
            "",
        ]
    )


def _validation_section(lines: list[str], validation: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 17 Validation Plan",
            "",
            f"- 状态：{_text(validation.get('status'))}",
            f"- Improvement Score：{_score_text(validation.get('improvement_score'))}",
            f"- 说明：{_text(validation.get('basis'))}",
            "",
        ]
    )
    for change in validation.get("metric_changes") or []:
        lines.append(
            f"- {_text(change.get('metric'))}：{_score_text(change.get('before'))} -> "
            f"{_score_text(change.get('after'))}（{_text(change.get('status'))}）"
        )
    if not (validation.get("metric_changes") or []):
        lines.append("- 没有真实 Before/After 数据，状态保持 UNKNOWN。")
    plan = validation.get("plan") or {}
    lines.extend(["", "复测步骤："])
    for step in plan.get("steps") or []:
        lines.append(f"- {step}")
    if plan.get("first_p0_verification"):
        lines.extend(["", f"首个 P0 验证：{_text(plan.get('first_p0_verification'))}"])
    lines.append("")


def _quality_section(lines: list[str], quality: dict[str, Any]) -> None:
    lines.extend(
        [
            "## 18 Data Quality",
            "",
            f"- Data Quality Score：{_score_text(quality.get('score'))}",
            f"- FACT：{quality.get('fact_count', 0)}；INFERENCE：{quality.get('inference_count', 0)}；UNKNOWN：{quality.get('unknown_count', 0)}",
            f"- 已核验：{quality.get('verified_count', 0)}；未核验：{quality.get('unverified_count', 0)}；来源数：{quality.get('source_count', 0)}",
            f"- Evidence Completeness：{_score_text(quality.get('evidence_completeness'))}",
            f"- Source Completeness：{_score_text(quality.get('source_completeness'))}",
            f"- Verification Completeness：{_score_text(quality.get('verification_completeness'))}",
            "",
        ]
    )
    if quality.get("warning"):
        lines.extend([f"> {_text(quality.get('warning'))}", ""])


def _unknown_section(lines: list[str], result: dict[str, Any]) -> None:
    lines.extend(["## 19 Unknown / Missing Data", ""])
    entity = result.get("entity") or {}
    missing = entity.get("missing") or []
    if missing:
        lines.append("企业字段仍为 UNKNOWN：")
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("企业实体已覆盖全部必查字段；仍需逐条核验来源。")
    evidence = (result.get("evidence_graph") or {}).get("items") or []
    missing_source = [item.get("id") for item in evidence if not item.get("source")]
    missing_date = [item.get("id") for item in evidence if not item.get("date")]
    if missing_source or missing_date:
        lines.extend(["", "Evidence 缺失：", f"- 缺少来源：{_join(missing_source) or '无'}", f"- 缺少日期：{_join(missing_date) or '无'}"])
    observations = (result.get("ai_cognition") or {}).get("observations") or []
    if not observations:
        lines.extend(["", "AI 观察缺失：尚未提供真实 AI 问答/搜索记录，所有认知结论均为 UNKNOWN。"])
    competitors = (result.get("competitors") or {}).get("competitors") or []
    if not competitors:
        lines.extend(["", "竞品缺失：没有可靠竞品数据；系统不会自动编造竞品。"])
    lines.extend(["", "客户还需补充："])
    for item in _required_materials(result):
        lines.append(f"- {item}")
    lines.append("")


def _critical_problems(result: dict[str, Any]) -> list[str]:
    gaps = (result.get("gaps") or {}).get("gaps") or []
    severe = [item for item in gaps if item.get("severity") in {"critical", "high"}]
    if not severe:
        severe = sorted(gaps, key=lambda item: _severity_rank(item.get("severity")), reverse=True)
    return [
        f"{item.get('type')}（{item.get('severity')}）：{item.get('reason')}"
        for item in severe[:3]
    ]


def _severity_rank(severity: Any) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(severity), 0)


def _required_materials(result: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    actions = (result.get("recommendations") or {}).get("actions") or []
    for priority in ("P0", "P1", "P2", "P3"):
        candidates = [action for action in actions if str(action.get("priority")) == priority]
        if not candidates:
            continue
        for action in candidates:
            for material in action.get("required_materials") or []:
                material = _text(material)
                if material and material not in seen:
                    seen.append(material)
        break
    return [f"{index + 1}. {item}" for index, item in enumerate(seen[:6])]


def _join(values: Iterable[Any]) -> str:
    return "、".join(str(value) for value in values if str(value) not in {"", "None", "UNKNOWN", "-"})


def _text(value: Any, fallback: str = "UNKNOWN") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _yes_no(value: Any) -> str:
    return "是" if value else "否"


def _score_text(value: Any) -> str:
    if value in (None, "", "None"):
        return "UNKNOWN"
    return str(value)
