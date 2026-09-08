"""InsightEngine turns a DiagnosticResult dict into a decision-first ReportModel.

The engine decides what matters, the ReportModel carries the structured answer,
and renderers only decide how to present that answer.
"""

from __future__ import annotations

import re
from typing import Any

from ..common import clamp, is_unknown
from .common import (
    entity_value,
    entity_values,
    evidence_items,
    observation_ids,
    query_list,
    rate_value,
    real_observations,
    source_type_label,
)
from .models import ReportModel
from .status import (
    CONFLICT,
    DERIVED,
    INSUFFICIENT_DATA,
    NOT_RUN,
    OBSERVED,
    PASS,
    PROVIDED,
    UNKNOWN,
    WARNING,
    metric,
    score_band,
)


GAP_TITLES = {
    "Entity Gap": "补齐企业基础实体资料",
    "Query Gap": "为高频推荐 Query 补齐内容",
    "Evidence Gap": "建立可核验证据包",
    "Experience Gap": "补充真实客户案例",
    "Authority Gap": "补充第三方权威证明",
    "Content Gap": "按场景补齐画像内容",
    "Citation Gap": "提升 AI 引用/采信率",
    "Trust Gap": "提升信任基础与来源核验",
    "Local/NAP Gap": "修复全网 NAP 冲突",
    "Competitor Gap": "缩小与竞品的可比差距",
}
TITLE_TO_GAP = {title: gap_type for gap_type, title in GAP_TITLES.items()}

GAP_AFFECTED_METRICS = {
    "Entity Gap": ["实体资料完整度", "官网露出", "电话露出"],
    "Query Gap": ["AI 推荐", "场景覆盖"],
    "Evidence Gap": ["AI 引用", "AI 可信度"],
    "Experience Gap": ["AI 认知", "AI 推荐"],
    "Authority Gap": ["AI 可信度", "AI 引用"],
    "Content Gap": ["AI 认知", "AI 推荐", "场景覆盖"],
    "Citation Gap": ["AI 引用"],
    "Trust Gap": ["AI 可信度", "AI 引用"],
    "Local/NAP Gap": ["官网露出", "电话露出"],
    "Competitor Gap": ["AI 推荐", "竞品差距"],
}

SEVERITY_IMPACT = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
}

INTENT_LABELS = {
    "informational": "信息型",
    "commercial": "商业调查型",
    "recommendation": "推荐型",
    "comparison": "对比型",
    "scenario": "场景型",
    "decision": "决策型",
    "local": "地域型",
    "brand": "品牌型",
    "product": "产品型",
    "problem": "问题型",
    "unknown": "未分类",
}

INTENT_METRIC_LABELS = {
    "ai_cognition": "AI认知",
    "ai_recommendation": "AI推荐",
    "ai_citation": "AI引用",
    "ai_trust": "AI可信度",
    "scenario_coverage": "场景覆盖",
}


class InsightEngine:
    def __init__(self, diagnostic: dict[str, Any] | None = None) -> None:
        self.d = diagnostic or {}

    def build(self, diagnostic: dict[str, Any] | None = None) -> ReportModel:
        if diagnostic is not None:
            self.d = diagnostic
        self.meta_block = self.d.get("meta") or {}
        self.company = self.d.get("company") or {}
        self.entity_block = self.d.get("entity") or {}
        self.cognition = self.d.get("ai_cognition") or {}
        self.matrix = self.d.get("query_matrix") or {}
        self.competitors = self.d.get("competitors") or {}
        self.graph = self.d.get("evidence_graph") or {}
        self.eeaap = self.d.get("eeaap") or {}
        self.eeat = self.d.get("eeat") or {}
        self.gaps_block = self.d.get("gaps") or {}
        self.opportunity_block = self.d.get("opportunities") or {}
        self.action_block = self.d.get("recommendations") or {}
        self.validation = self.d.get("validation") or {}
        self.scores = self.d.get("scores") or {}
        self.quality = self.d.get("data_quality") or {}
        self.scenarios = self.d.get("scenarios") or {}
        self.citations = self.d.get("citations") or {}
        self.nap = self.d.get("nap") or {}
        self.obs = real_observations(self.d)
        self.evidence = evidence_items(self.d)
        self.matrix_queries = query_list(self.d)
        self.gaps = list((self.gaps_block).get("gaps") or [])
        self.v2_opportunities = list((self.opportunity_block).get("opportunities") or [])
        self.v2_actions = list((self.action_block).get("actions") or [])
        self.company_name = (
            entity_value(self.entity_block, "name")
            or str(self.company.get("name") or "").strip()
            or "该企业"
        )
        self.report_confidence = self._report_confidence()
        self.has_diagnostic_content = self._has_diagnostic_content()
        self.all_problems = self._build_problems() if self.has_diagnostic_content else []
        problems_by_gap = {item["source_gap_type"]: item for item in self.all_problems}
        self.problems_by_gap = problems_by_gap
        return ReportModel(
            meta=self._meta(),
            health=self._health(),
            core_metrics=self._core_metrics(),
            ai_cognition=self._ai_cognition(),
            top_problems=self.all_problems[:3],
            opportunities=self._opportunities(),
            action_plan=self._actions(),
            query_clusters=self._query_clusters(),
            competitor_summary=self._competitor_summary(),
            entity_consistency=self._entity_consistency(),
            evidence_conflicts=self._evidence_conflicts(),
            baseline=self._baseline(),
            measurement=self._measurement(),
            evidence_refs=[
                {
                    "id": str(item.get("id") or ""),
                    "claim": str(item.get("claim") or "").strip(),
                    "source": str(item.get("source") or "").strip(),
                    "source_type": str(item.get("source_type") or "unknown"),
                    "source_type_label": source_type_label(item.get("source_type")),
                    "date": str(item.get("date") or "").strip(),
                    "verified": bool(item.get("verified")),
                    "confidence": item.get("confidence"),
                    "status": str(item.get("status") or UNKNOWN),
                    "conflicts_with": list(item.get("conflicts_with") or []),
                    "category": str(item.get("category") or "").strip(),
                }
                for item in self.evidence
            ],
            confidence=self._confidence(),
        )

    def _has_diagnostic_content(self) -> bool:
        """Real input exists when any entity value, observation, evidence or query is present."""
        if self.obs or self.evidence or self.matrix_queries:
            return True
        for raw_values in (self.entity_block.get("fields") or {}).values():
            values = raw_values if isinstance(raw_values, list) else [raw_values]
            for item in values:
                if isinstance(item, dict):
                    value = item.get("value")
                else:
                    value = item
                if not is_unknown(value):
                    return True
        return False

    def _meta(self) -> dict[str, Any]:
        return {
            "engine": str(self.meta_block.get("engine") or "GEO Diagnostic Engine"),
            "version": str(self.meta_block.get("version") or "3.0.0"),
            "generated_at": str(self.meta_block.get("generated_at") or ""),
            "research_mode": str(self.meta_block.get("research_mode") or UNKNOWN),
            "company_name": self.company_name,
            "diagnostic_note": str(
                self.meta_block.get("diagnostic_note")
                or "Score is a diagnostic indicator, not a ranking guarantee."
            ),
        }

    def _health(self) -> dict[str, Any]:
        score = self.scores.get("geo_score")
        score = score if isinstance(score, (int, float)) and not isinstance(score, bool) else None
        score = clamp(score) if score is not None else None
        status = str(self.scores.get("status") or UNKNOWN)
        if score is None and status != INSUFFICIENT_DATA:
            status = INSUFFICIENT_DATA if not self.obs and not self.evidence else UNKNOWN
        band_data = score_band(score)
        band = band_data[0] if band_data else UNKNOWN
        band_label = band_data[1] if band_data else "没有足够数据形成 GEO 判断"
        summary = self._executive_summary(score, band)
        basis = ""
        if isinstance(self.scores.get("basis"), dict):
            basis = str((self.scores.get("basis") or {}).get("geo_score") or "")
        return {
            "score": score,
            "status": status,
            "band": band,
            "band_label": band_label,
            "summary": summary,
            "basis": basis,
            "data_completeness": self.scores.get("data_completeness"),
            "available_dimensions": list(self.scores.get("available_dimensions") or []),
            "insufficient_dimensions": list(self.scores.get("insufficient_dimensions") or []),
        }

    def _executive_summary(self, score: int | None, band: str) -> str:
        if not self.obs:
            if not self.company_name or self.company_name == "该企业":
                return (
                    "当前只能进行基础数据检查，无法进行完整 GEO 或 AI 表现判断；"
                    "请先补充企业资料、Evidence 与真实 AI Observation。"
                )
            return (
                f"{self.company_name} 当前只能进行基础实体诊断，无法进行完整 AI 表现判断；"
                "请先补充真实 AI Observation 后再评估 AI 认知、推荐与引用。"
            )
        observed_queries = len(self.obs)
        recommended = sum(1 for item in self.obs if item.get("company_recommended"))
        cited = sum(1 for item in self.obs if item.get("company_cited"))
        score_text = f"{score}/100" if score is not None else "无法计算"
        recognized = (
            f"AI 已能识别 {self.company_name}：在 {observed_queries} 条真实观察中，"
            f"{sum(1 for item in self.obs if item.get('company_mentioned'))} 条提及、"
            f"{recommended} 条推荐、{cited} 条引用企业。"
        )
        gap = self._cognition_gap_text()
        return f"{self.company_name} 当前 GEO 状态为 {band}（{score_text}）。{recognized} 当前最大的认知缺口：{gap}"

    def _core_metrics(self) -> dict[str, Any]:
        coverage = self.matrix.get("coverage") or {}
        ai_basis = str(self.cognition.get("basis") or "")
        if self.obs:
            cognition_value = self.scores.get("ai_cognition_score")
            cognition_value = cognition_value if isinstance(cognition_value, (int, float)) else None
            cognition_status = OBSERVED if all(
                str(item.get("observation_mode") or "observed") != "provided" for item in self.obs
            ) else PROVIDED
            cognition_basis = ai_basis or "基于真实 AI 观察结果综合计算。"
        else:
            cognition_value = None
            cognition_status = UNKNOWN
            cognition_basis = "当前没有真实 AI Observation 数据；不估算 AI 认知分数。"

        recommendation = self._rate_metric("recommendation_rate", "AI 推荐")
        citation = self._rate_metric("citation_rate", "AI 引用")

        trust_score = self.scores.get("trust_score")
        if isinstance(trust_score, (int, float)) and not isinstance(trust_score, bool):
            trust = metric(
                clamp(trust_score),
                DERIVED,
                str((self.scores.get("basis") or {}).get("trust_score") or self._eeat_basis("trustworthiness"))
                or "由 Evidence 核验、第三方来源与 NAP 一致性计算。",
                unit="score",
            )
        else:
            trust = metric(
                None,
                UNKNOWN,
                "没有足够的证据核验与 NAP 数据，无法判断 AI 可信度。",
                unit="score",
            )

        scenario_value = self.scenarios.get("scenario_coverage_score")
        scenario_status = str(self.scenarios.get("status") or self.scenarios.get("scenario_status") or UNKNOWN)
        if isinstance(scenario_value, (int, float)) and scenario_status in {"COMPUTED", "OBSERVED"}:
            scenario = metric(
                clamp(scenario_value),
                OBSERVED if self.obs else PROVIDED,
                str(self.scenarios.get("basis") or "基于同一批 Query 的真实观察计算。"),
                unit="rate",
            )
        else:
            scenario = metric(
                None,
                NOT_RUN if scenario_status == NOT_RUN else UNKNOWN,
                "当前没有可计量的真实场景观察；不估算场景覆盖。",
                unit="rate",
            )

        result = {
            "ai_cognition": metric(cognition_value, cognition_status, cognition_basis, unit="score"),
            "ai_recommendation": recommendation,
            "ai_citation": citation,
            "ai_trust": trust,
            "scenario_coverage": scenario,
        }
        result["_labels"] = INTENT_METRIC_LABELS
        result["coverage"] = {
            "status": str(coverage.get("status") or UNKNOWN),
            "mention_rate": rate_value(coverage, "mention_rate"),
            "recommendation_rate": rate_value(coverage, "recommendation_rate"),
            "description_accuracy": rate_value(coverage, "description_accuracy"),
            "citation_rate": rate_value(coverage, "citation_rate"),
            "scenario_coverage": rate_value(coverage, "scenario_coverage"),
            "score": rate_value(coverage, "score"),
            "basis": str(coverage.get("basis") or ""),
        }
        return result

    def _rate_metric(self, key: str, label: str) -> dict[str, Any]:
        value = rate_value(self.citations, key)
        basis = str(self.citations.get("basis") or "")
        source = "citations"
        if value is None and str(self._ai_tests_block_status()) in {"COMPUTED", "OBSERVED"}:
            value = rate_value(self.d.get("ai_tests") or {}, key)
            basis = str((self.d.get("ai_tests") or {}).get("basis") or basis)
            source = "ai_tests"
        if value is None:
            coverage = self.matrix.get("coverage") or {}
            if str(coverage.get("status") or "") in {"COMPUTED", "OBSERVED"}:
                value = rate_value(coverage, key)
                basis = str(coverage.get("basis") or basis)
                source = "query_matrix.coverage"
        if value is None or not self.obs:
            status = UNKNOWN
            basis = f"当前没有真实 AI Observation 数据，无法判断{label}。"
        else:
            status = OBSERVED if source in {"citations", "ai_tests", "query_matrix.coverage"} else PROVIDED
        return metric(value, status, basis, unit="rate")

    def _ai_tests_block_status(self) -> str:
        return str((self.d.get("ai_tests") or {}).get("status") or NOT_RUN)

    def _ai_cognition(self) -> dict[str, Any]:
        status = OBSERVED if self.obs else UNKNOWN
        recognized: list[str] = []
        not_recognized: list[str] = []
        if self.obs:
            if any(item.get("company_mentioned") for item in self.obs):
                recognized.append("AI 能提及企业")
            else:
                not_recognized.append("在真实观察中没有出现企业提及")
            if any(item.get("company_recommended") for item in self.obs):
                recognized.append("AI 愿意推荐企业")
            else:
                not_recognized.append("AI 尚未明确推荐企业")
            if any(item.get("company_correctly_described") for item in self.obs):
                recognized.append("AI 能较准确地描述企业")
            else:
                not_recognized.append("AI 对企业的描述准确性尚无法确认")
            if any(item.get("company_cited") for item in self.obs):
                recognized.append("AI 会引用企业来源")
            else:
                not_recognized.append("真实观察中尚未出现企业来源引用")
        gap = self._cognition_gap_text()
        observation_rows = [
            {
                "query": str(item.get("query") or "").strip(),
                "query_type": str(item.get("query_type") or "unknown"),
                "company_mentioned": bool(item.get("company_mentioned")),
                "company_recommended": bool(item.get("company_recommended")),
                "company_correctly_described": bool(item.get("company_correctly_described")),
                "company_cited": bool(item.get("company_cited")),
                "position": item.get("position"),
                "observation_mode": str(item.get("observation_mode") or "observed"),
                "sources": list(item.get("sources") or []),
            }
            for item in self.obs
        ]
        return {
            "status": status,
            "observation_count": len(self.obs),
            "observation_ids": observation_ids(self.obs),
            "observations": observation_rows,
            "recognized": recognized,
            "not_recognized": not_recognized,
            "gap": gap,
            "summary": self._cognition_summary(recognized, not_recognized, gap),
            "basis": str(self.cognition.get("basis") or ""),
        }

    def _cognition_summary(self, recognized: list[str], not_recognized: list[str], gap: str) -> str:
        if not self.obs:
            return (
                f"当前没有真实 AI Observation 数据，无法判断 AI 是否认识 {self.company_name}；"
                "完成第一轮真实 Query 测试后才能建立认知基线。"
            )
        if recognized:
            recognized_text = "、".join(recognized[:2])
            if not_recognized:
                return f"AI 已经能够做到：{recognized_text}。仍需关注：{not_recognized[0]}。"
            return f"AI 在现有真实观察中已经能够做到：{recognized_text}。{gap}"
        return f"AI 在现有真实观察中尚未形成稳定识别；{gap}"

    def _cognition_gap_text(self) -> str:
        if not self.obs:
            return "缺少真实 AI Observation，无法判断核心认知缺口。"
        gap_scores = {
            str(gap.get("type") or ""): gap
            for gap in self.gaps
        }
        for gap_type in ("Content Gap", "Trust Gap", "Evidence Gap", "Competitor Gap", "Local/NAP Gap"):
            gap = gap_scores.get(gap_type)
            if gap and str(gap.get("reason") or "").strip():
                return str(gap.get("reason") or "").strip()
        return "现有观察样本有限，需要扩大 Query 覆盖后再判断核心认知缺口。"

    def _build_problems(self) -> list[dict[str, Any]]:
        opportunity_by_gap = self._opportunity_by_gap()
        ranked = sorted(
            self.gaps,
            key=lambda gap: (
                int(gap.get("score") or 0),
                self._opportunity_rank(str(gap.get("type") or ""), opportunity_by_gap),
                self._severity_rank(gap.get("severity")),
            ),
            reverse=True,
        )
        problems: list[dict[str, Any]] = []
        for index, gap in enumerate(ranked[:10], start=1):
            gap_type = str(gap.get("type") or "Unknown Gap")
            opportunity = self._matching_opportunity(gap_type, opportunity_by_gap)
            priority = str(opportunity.get("priority") or self._severity_priority(gap.get("severity")))
            score = int(gap.get("score") or 0)
            severity_value = SEVERITY_IMPACT.get(str(gap.get("severity") or "").lower(), 2)
            impact = max(1, min(5, round(max(score, severity_value * 20) / 20)))
            trace = self._gap_trace(gap_type, gap)
            problems.append(
                {
                    "id": f"P{index:03d}",
                    "priority": priority,
                    "title": GAP_TITLES.get(gap_type, gap_type),
                    "impact": impact,
                    "confidence": self.report_confidence,
                    "why_it_matters": str(gap.get("reason") or "诊断数据不足以解释该问题。").strip(),
                    "affected_metrics": GAP_AFFECTED_METRICS.get(gap_type, ["GEO Score"]),
                    "evidence_ids": trace["evidence_ids"],
                    "observation_ids": trace["observation_ids"],
                    "query_ids": trace["query_ids"],
                    "source_ids": trace["source_ids"],
                    "source_gap_type": gap_type,
                    "severity": str(gap.get("severity") or UNKNOWN),
                    "score": score,
                }
            )
        return problems

    def _opportunity_rank(self, gap_type: str, opportunity_by_gap: dict[str, dict[str, Any]]) -> int:
        opportunity = opportunity_by_gap.get(gap_type) or {}
        value = opportunity.get("score")
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0

    def _opportunities(self) -> list[dict[str, Any]]:
        if not self.has_diagnostic_content:
            return []
        opportunity_by_gap = self._opportunity_by_gap()
        coverage = self.matrix.get("coverage") or {}
        current_presence = (
            rate_value(coverage, "recommendation_rate")
            if self.obs and str(coverage.get("status") or "") in {"OBSERVED", "COMPUTED"}
            else None
        )
        current_presence_status = OBSERVED if current_presence is not None else UNKNOWN
        results: list[dict[str, Any]] = []
        for index, item in enumerate(self.v2_opportunities[:10], start=1):
            title = str(item.get("title") or "")
            gap_type = TITLE_TO_GAP.get(title, title)
            gap = next((g for g in self.gaps if str(g.get("type") or "") == gap_type), {})
            trace = self._gap_trace(gap_type, gap)
            problem = self.problems_by_gap.get(gap_type)
            results.append(
                {
                    "id": f"O{index:03d}",
                    "title": title,
                    "opportunity_index": item.get("score"),
                    "priority": str(item.get("priority") or "P2"),
                    "business_value": item.get("business_value"),
                    "ai_opportunity": item.get("ai_demand"),
                    "competition": item.get("competitor_gap"),
                    "feasibility": item.get("feasibility"),
                    "evidence_availability": item.get("evidence_availability"),
                    "current_presence": current_presence,
                    "current_presence_status": current_presence_status,
                    "gap": gap.get("score"),
                    "reason": str(item.get("reason") or ""),
                    "status": str(item.get("status") or INFERENCE_LABEL()),
                    "evidence_ids": trace["evidence_ids"],
                    "observation_ids": trace["observation_ids"],
                    "query_ids": trace["query_ids"],
                    "source_ids": trace["source_ids"],
                    "source_problem_ids": [problem["id"]] if problem else [],
                    "source_gap_type": gap_type,
                }
            )
        return results

    def _actions(self) -> list[dict[str, Any]]:
        if not self.has_diagnostic_content:
            return []
        opportunity_by_gap = self._opportunity_by_gap()
        results: list[dict[str, Any]] = []
        for index, action in enumerate(self.v2_actions, start=1):
            title = str(action.get("task") or "")
            gap_type = TITLE_TO_GAP.get(title, title)
            opportunity = self._matching_opportunity(gap_type, opportunity_by_gap)
            if opportunity:
                impact_value = opportunity.get("business_value")
                feasibility = opportunity.get("feasibility")
                effort = "low" if isinstance(feasibility, (int, float)) and feasibility >= 80 else "medium" if isinstance(
                    feasibility, (int, float)
                ) and feasibility >= 65 else "high"
            else:
                gap = next((g for g in self.gaps if str(g.get("type") or "") == gap_type), {})
                impact_value = 70 if self._severity_rank(gap.get("severity")) >= 3 else 55
                effort = "medium"
            gap = next((g for g in self.gaps if str(g.get("type") or "") == gap_type), {})
            trace = self._gap_trace(gap_type, gap)
            problem = self.problems_by_gap.get(gap_type)
            tasks = [str(action.get("action") or title)]
            for material in action.get("required_materials") or []:
                if str(material or "").strip():
                    tasks.append(f"准备资料：{material}")
            if str(action.get("verification") or "").strip():
                tasks.append(f"验证：{action.get('verification')}")
            expected_impact = list(action.get("impact") or []) or GAP_AFFECTED_METRICS.get(gap_type, ["GEO Score"])
            results.append(
                {
                    "id": f"A{index:03d}",
                    "priority": str(action.get("priority") or "P2"),
                    "title": title,
                    "objective": str(action.get("problem") or action.get("why") or ""),
                    "tasks": tasks,
                    "expected_impact": expected_impact,
                    "effort": effort,
                    "impact": impact_value,
                    "confidence": self.report_confidence,
                    "evidence_ids": trace["evidence_ids"],
                    "observation_ids": trace["observation_ids"],
                    "query_ids": trace["query_ids"],
                    "source_ids": trace["source_ids"],
                    "source_problem_ids": [problem["id"]] if problem else [],
                    "required_materials": list(action.get("required_materials") or []),
                    "verification": str(action.get("verification") or ""),
                    "heuristics": list(action.get("source_doc_heuristics") or []),
                    "source_gap_type": gap_type,
                }
            )
        return results

    def _query_clusters(self) -> list[dict[str, Any]]:
        coverage = self.matrix.get("coverage") or {}
        rows = [
            {
                "query": str(query.get("query") or "").strip(),
                "intent": str(query.get("intent") or "unknown"),
            }
            for query in self.matrix_queries
            if str(query.get("query") or "").strip()
        ]
        seen_queries = {row["query"] for row in rows}
        for observation in self.obs:
            query = str(observation.get("query") or "").strip()
            if not query or query in seen_queries:
                continue
            rows.append({"query": query, "intent": str(observation.get("query_type") or "unknown")})
            seen_queries.add(query)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["intent"], []).append(row)
        clusters: list[dict[str, Any]] = []
        for intent, queries in sorted(grouped.items()):
            rates = None
            status = str(coverage.get("status") or UNKNOWN)
            if status in {"OBSERVED", "COMPUTED"}:
                rates = {
                    "mention_rate": rate_value(coverage, "mention_rate"),
                    "recommendation_rate": rate_value(coverage, "recommendation_rate"),
                    "description_accuracy": rate_value(coverage, "description_accuracy"),
                    "citation_rate": rate_value(coverage, "citation_rate"),
                    "scenario_coverage": rate_value(coverage, "scenario_coverage"),
                    "score": rate_value(coverage, "score"),
                }
            clusters.append(
                {
                    "intent": intent,
                    "label": INTENT_LABELS.get(intent, intent),
                    "query_count": len(queries),
                    "query_ids": [str(q.get("query") or "") for q in queries if str(q.get("query") or "").strip()],
                    "rates": rates,
                    "status": status,
                    "basis": str(coverage.get("basis") or ""),
                }
            )
        if not clusters:
            return []
        return clusters

    def _competitor_summary(self) -> dict[str, Any]:
        competitor_items = list(self.competitors.get("competitors") or [])
        if not self.obs:
            basis = (
                "有确认竞品清单，但没有真实 AI Observation 可比数据，竞品 AI 指标不评分。"
                if competitor_items
                else "没有真实 AI Observation，竞品 AI 指标不评分；请先补充真实 Observation 与确认竞品清单。"
            )
            return {
                "status": UNKNOWN,
                "share_of_voice": {
                    "status": UNKNOWN,
                    "basis": "没有真实 AI Observation，无法计算 AI Share of Voice；不采用人工推测数据。",
                    "items": [],
                },
                "competitors": [
                    {
                        "name": str(item.get("name") or ""),
                        "status": str(item.get("status") or UNKNOWN),
                        "mention_rate": None,
                        "recommendation_rate": None,
                        "evidence_count": None,
                        "authority_score": None,
                        "citation_rate": None,
                        "sources": list(item.get("sources") or []),
                    }
                    for item in competitor_items
                ],
                "gap_edges": [],
                "gap_count": 0,
                "basis": basis,
            }
        gap_matrix = list(self.competitors.get("gap_matrix") or [])
        block_status = str(self.competitors.get("status") or UNKNOWN)
        share, share_status, share_basis = self._share_of_voice()
        share_items = (
            [
                {
                    "name": name,
                    "share": share_value,
                    "mentioned_in": count,
                }
                for name, (count, share_value) in share.items()
            ]
            if share is not None
            else []
        )
        gaps = [
            {
                "dimension": str(item.get("dimension") or ""),
                "client_score": item.get("client_score"),
                "competitor_score": item.get("competitor_score"),
                "gap": item.get("gap"),
                "status": str(item.get("status") or UNKNOWN),
                "basis": str(item.get("basis") or ""),
            }
            for item in gap_matrix
            if item.get("status") == "COMPUTED"
        ]
        return {
            "status": block_status,
            "share_of_voice": {
                "status": share_status,
                "basis": share_basis,
                "items": share_items,
            },
            "competitors": [
                {
                    "name": str(item.get("name") or ""),
                    "status": str(item.get("status") or UNKNOWN),
                    "mention_rate": item.get("mention_rate"),
                    "recommendation_rate": item.get("recommendation_rate"),
                    "evidence_count": item.get("evidence_count"),
                    "authority_score": item.get("authority_score"),
                    "citation_rate": item.get("citation_rate"),
                    "sources": list(item.get("sources") or []),
                }
                for item in competitor_items
            ],
            "gap_edges": gaps,
            "gap_count": len(gaps),
            "basis": str(self.competitors.get("basis") or ""),
        }

    def _share_of_voice(self) -> tuple[dict[str, tuple[int, float]] | None, str, str]:
        if not self.obs:
            return None, UNKNOWN, "没有真实 AI Observation，无法计算 AI Share of Voice；不采用人工推测数据。"
        counts: dict[str, int] = {}
        for item in self.obs:
            if item.get("company_mentioned") or item.get("company_recommended"):
                counts.setdefault(self.company_name, 0)
                counts[self.company_name] += 1
            for competitor in item.get("competitors_mentioned") or []:
                name = str(competitor or "").strip()
                if name:
                    counts[name] = counts.get(name, 0) + 1
        total = sum(counts.values())
        if not total:
            return None, UNKNOWN, "真实观察中没有可计数的企业或竞品提及。"
        shares = {
            name: (count, round(count * 100 / total, 1))
            for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
        }
        return (
            shares,
            OBSERVED,
            "基于真实 AI 回答中的企业/竞品被提及次数计算，不把用户填写的竞品指标当作 AI 观察。",
        )

    def _entity_consistency(self) -> dict[str, Any]:
        fields = self.entity_block.get("fields") or {}
        nap_fields = self.nap.get("fields") or {}
        issues = [str(item) for item in (self.company.get("issues") or []) if str(item).strip()]
        conflicts = [str(item) for item in (self.nap.get("conflicts") or []) if str(item).strip()]
        issue_text = " ".join([*issues, *conflicts])

        def item_status(label: str, value: Any) -> str:
            value = str(value or "").strip()
            if not value or is_unknown(value):
                return UNKNOWN
            if label in issue_text and any(word in issue_text for word in ("冲突", "不一致", "矛盾")):
                return CONFLICT
            if label in issue_text:
                return WARNING
            return PASS

        known_value = lambda key, nap_key=None: str(  # noqa: E731
            nap_fields.get(nap_key or key) or entity_value(self.entity_block, key)
        ).strip()
        name = known_value("name")
        phone = known_value("phone", "phone") or known_value("contacts", "phone")
        website = known_value("website")
        address = known_value("address")
        aliases = "、".join(entity_values(self.entity_block, "aliases"))
        brands = "、".join(entity_values(self.entity_block, "brands"))
        products = "、".join(entity_values(self.entity_block, "products"))
        services = "、".join(entity_values(self.entity_block, "services"))
        values = {
            "name": (name, item_status("公司名称", name)),
            "aliases": (aliases or name, item_status("别名", aliases)),
            "brands": (brands, item_status("品牌", brands)),
            "website": (website, item_status("官网", website)),
            "phone": (phone, item_status("电话", phone)),
            "address": (address, item_status("地址", address)),
            "products": (products, item_status("产品", products)),
            "services": (services, item_status("服务", services)),
        }
        rows = [
            {"field": key, "value": value, "status": status}
            for key, (value, status) in values.items()
        ]
        if any(row["status"] == CONFLICT for row in rows):
            overall = CONFLICT
        elif any(row["status"] == WARNING for row in rows):
            overall = WARNING
        elif any(row["status"] == UNKNOWN for row in rows):
            overall = UNKNOWN if not any(row["status"] == PASS for row in rows) else WARNING
        else:
            overall = PASS
        summary = self._entity_summary(overall, rows)
        return {
            "status": overall,
            "fields": rows,
            "summary": summary,
            "nap_consistent": self.nap.get("consistent"),
            "nap_complete": self.nap.get("complete"),
            "issues": issues,
            "conflicts": conflicts,
            "basis": str(self.nap.get("basis") or ""),
        }

    def _entity_summary(self, overall: str, rows: list[dict[str, Any]]) -> str:
        missing = [row["field"] for row in rows if row["status"] in {UNKNOWN, WARNING}]
        if overall == CONFLICT:
            return "企业主体信息存在冲突，AI 可能因此无法安全露出官网、电话或地址。"
        if missing:
            labels = "、".join(missing[:5])
            return f"企业主体信息仍有缺口或需核验（{labels}），建议先统一后再做真实 AI 复测。"
        return "企业主体信息在现有输入内保持一致；仍需结合真实 AI 观察复测露出。"

    def _evidence_conflicts(self) -> dict[str, Any]:
        item_conflicts = []
        for item in self.evidence:
            targets = [str(value) for value in (item.get("conflicts_with") or []) if str(value).strip()]
            if targets:
                item_conflicts.append(
                    {
                        "evidence_id": str(item.get("id") or ""),
                        "claim": str(item.get("claim") or ""),
                        "conflicts_with": targets,
                        "source": str(item.get("source") or ""),
                    }
                )
        nap_conflicts = [str(item) for item in (self.nap.get("conflicts") or []) if str(item).strip()]
        conflicts = item_conflicts
        if nap_conflicts:
            conflicts.append(
                {
                    "evidence_id": "NAP",
                    "claim": "Name/Address/Phone 存在冲突或露出问题",
                    "conflicts_with": nap_conflicts,
                    "source": "用户上报/平台核验",
                }
            )
        if conflicts:
            status = CONFLICT
            summary = "发现需要建立 Canonical Source 的证据或 NAP 冲突。"
        elif self.evidence:
            status = "NONE"
            summary = "现有 Evidence 之间未检测到 conflicts_with 冲突。"
        else:
            status = UNKNOWN
            summary = "没有 Evidence 记录，无法检测证据冲突。"
        return {
            "status": status,
            "summary": summary,
            "conflicts": conflicts,
            "count": len(conflicts),
        }

    def _baseline(self) -> dict[str, Any]:
        before = self.validation.get("before_metrics") or {}
        after = self.validation.get("after_metrics") or {}
        before = {key: value for key, value in before.items() if not is_unknown(value)}
        after = {key: value for key, value in after.items() if not is_unknown(value)}
        has_before = bool(before)
        has_after = bool(after)
        if has_after and has_before:
            status = "COMPARISON_READY"
            summary = "已具备 Before/After 指标，可比较 GEO 变化。"
        elif has_before:
            status = "BASELINE_ONLY"
            summary = "已有用户提供的 Before 指标；完成真实 AI 复测后写入 After 再做对比。"
        else:
            status = "NOT_ESTABLISHED"
            summary = "尚未建立基线；建议完成第一轮真实 AI Observation 后建立 Baseline。"
        return {
            "status": status,
            "summary": summary,
            "before_metrics": before,
            "after_metrics": after,
        }

    def _measurement(self) -> dict[str, Any]:
        baseline = self._baseline()
        changes = list(self.validation.get("metric_changes") or [])
        plan = self.validation.get("plan") or {}
        if baseline["status"] == "COMPARISON_READY" and not changes:
            changes = self._metric_changes(baseline["before_metrics"], baseline["after_metrics"])
        return {
            "status": str(self.validation.get("status") or UNKNOWN),
            "improvement_score": self.validation.get("improvement_score"),
            "metric_changes": changes,
            "plan_steps": list(plan.get("steps") or []),
            "first_p0_verification": str(plan.get("first_p0_verification") or ""),
            "baseline_status": baseline["status"],
        }

    def _metric_changes(self, before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        labels = {
            "mention_rate": "Mention Rate",
            "recommendation_rate": "Recommendation Rate",
            "citation_rate": "Citation Rate",
            "query_coverage": "Query Coverage",
            "ai_share_of_voice": "AI Share of Voice",
        }
        for key in sorted(set(before) & set(after)):
            try:
                before_value = float(before[key])
                after_value = float(after[key])
            except (TypeError, ValueError):
                continue
            changes.append(
                {
                    "metric": labels.get(str(key), str(key)),
                    "before": before_value,
                    "after": after_value,
                    "delta": round(after_value - before_value, 1),
                    "status": "IMPROVED" if after_value > before_value else "DECLINED" if after_value < before_value else "UNCHANGED",
                }
            )
        return changes

    def _confidence(self) -> dict[str, Any]:
        missing: list[str] = []
        if not self.obs:
            missing.append("真实 AI Observation（AI 认知/推荐/引用都需要它）")
        if not self.evidence:
            missing.append("Evidence（声明、来源、日期与核验状态）")
        if not (self.competitors.get("competitors") or []):
            missing.append("确认竞品清单（未提供时不编造竞品）")
        if not self.matrix_queries:
            missing.append("Query Matrix（高频业务问题）")
        for key in self.entity_block.get("missing") or []:
            missing.append(f"企业字段：{key}")
        seen: list[str] = []
        for item in missing:
            if item not in seen:
                seen.append(item)
        quality_score = self.quality.get("score")
        dimension_label = "高可信" if self.report_confidence >= 0.85 else "中高可信" if self.report_confidence >= 0.65 else "中等可信" if self.report_confidence >= 0.5 else "低可信"
        return {
            "score": round(self.report_confidence * 100),
            "confidence": self.report_confidence,
            "label": dimension_label,
            "status": "COMPUTED" if self.report_confidence > 0 else UNKNOWN,
            "data_quality_score": quality_score,
            "missing_data": seen,
            "basis": str(self.quality.get("warning") or "")
            or "可信度代表当前诊断结论基于现有证据的可靠程度，不代表 AI 平台真实排名或事实正确率。",
            "disclaimer": (
                "不要把 confidence 当成事实正确率；它只表示当前诊断结论基于现有证据的可信程度。"
            ),
        }

    def _report_confidence(self) -> float:
        confidence = self.scores.get("confidence")
        try:
            value = float(confidence) if confidence is not None else 0.0
        except (TypeError, ValueError):
            value = 0.0
        if value <= 0:
            quality_score = self.quality.get("score")
            try:
                return clamp(float(quality_score) if quality_score is not None else 0.0) / 100
            except (TypeError, ValueError):
                return 0.0
        return max(0.0, min(1.0, value))

    def _opportunity_by_gap(self) -> dict[str, dict[str, Any]]:
        return {
            TITLE_TO_GAP.get(str(item.get("title") or ""), str(item.get("title") or "")): item
            for item in self.v2_opportunities
            if str(item.get("title") or "").strip()
        }

    def _matching_opportunity(self, gap_type: str, opportunity_by_gap: dict[str, dict[str, Any]]) -> dict[str, Any]:
        return opportunity_by_gap.get(gap_type) or {}

    def _gap_trace(self, gap_type: str, gap: dict[str, Any]) -> dict[str, list[str]]:
        query_ids = [str(item) for item in (gap.get("affected_queries") or []) if str(item).strip()]
        evidence_ids = self._evidence_ids_for_gap(gap_type, gap)
        obs_ids: list[str] = []
        source_values: list[str] = []
        if self.obs and gap_type in {
            "Query Gap",
            "Content Gap",
            "Citation Gap",
            "Trust Gap",
            "Competitor Gap",
            "Local/NAP Gap",
        }:
            obs_ids = observation_ids(self.obs)
        if not query_ids:
            query_ids = [str(item.get("query") or "") for item in self.matrix_queries if str(item.get("query") or "").strip()]
        for item in self.evidence:
            if item.get("source"):
                source_values.append(str(item.get("source")).strip())
        for observation in self.obs:
            source_values.extend(str(source or "") for source in observation.get("sources") or [])
        if not evidence_ids and not query_ids and not obs_ids and not source_values:
            if self.entity_block.get("fields"):
                source_values.append("用户提供资料")
        unique = lambda values: list(dict.fromkeys([value for value in values if value]))  # noqa: E731
        return {
            "evidence_ids": unique(evidence_ids),
            "observation_ids": unique(obs_ids),
            "query_ids": unique(query_ids),
            "source_ids": unique(source_values),
        }

    def _evidence_ids_for_gap(self, gap_type: str, gap: dict[str, Any]) -> list[str]:
        texts = [str(gap.get("reason") or "")]
        basis = self.eeaap.get("basis") if isinstance(self.eeaap.get("basis"), dict) else {}
        eeat_basis = self.eeat.get("basis") if isinstance(self.eeat.get("basis"), dict) else {}
        if gap_type in {
            "Evidence Gap",
            "Experience Gap",
            "Authority Gap",
            "Content Gap",
            "Citation Gap",
            "Trust Gap",
        }:
            texts.extend(str(value) for value in basis.values())
            texts.extend(str(value) for value in eeat_basis.values())
        parsed: list[str] = []
        for text in texts:
            parsed.extend(re.findall(r"E\d{3,}", text))
        unique = list(dict.fromkeys(parsed))
        if unique:
            return unique
        categories: dict[str, list[str]] = {
            "Evidence Gap": [],
            "Trust Gap": [],
            "Content Gap": [],
            "Citation Gap": [],
            "Experience Gap": ["experience", "case"],
            "Authority Gap": ["authoritativeness", "accuracy", "perspective"],
        }
        if gap_type in categories:
            allowed = categories[gap_type]
            if allowed:
                return [str(item.get("id") or "") for item in self.evidence if str(item.get("category") or "") in allowed]
            return [str(item.get("id") or "") for item in self.evidence]
        return []

    def _severity_rank(self, severity: Any) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(severity).lower(), 0)

    def _severity_priority(self, severity: Any) -> str:
        return {"critical": "P0", "high": "P1", "medium": "P2", "low": "P3"}.get(str(severity).lower(), "P2")

    def _eeat_basis(self, key: str) -> str:
        basis = self.eeat.get("basis")
        if isinstance(basis, dict):
            return str(basis.get(key) or "")
        return ""


def INFERENCE_LABEL() -> str:
    return "INFERENCE"
