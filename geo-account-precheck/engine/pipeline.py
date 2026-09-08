"""End-to-end GEO diagnostic pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import __version__
from .ai_test import analyze_ai_tests
from .cognition.analyzer import CognitionAnalyzer
from .cognition.query_builder import build_cognition_queries
from .common import FACT, UNKNOWN, to_dict
from .competitor.analyzer import CompetitorAnalyzer
from .eeaap.scorer import EeaapScorer
from .eeat.scorer import EeatScorer
from .entity.researcher import EntityResearcher
from .evidence.graph import build_evidence_graph
from .evidence.verifier import EvidenceVerifier
from .enterprise_intelligence import build_competition_intelligence
from .gap.analyzer import analyze_gaps
from .models.company import CompanyProfile
from .models.competitor import Competitor
from .models.evidence import EvidenceItem
from .models.report import DiagnosticResult
from .providers import ManualProvider, OfflineProvider, ResearchProvider
from .quality import compute_data_quality
from .query.matrix import QueryMatrix
from .recommendation.planner import RecommendationPlanner
from .scorecard import build_scorecard
from .scoring.opportunity import OpportunityScorer
from .summary import (
    build_citation_block,
    build_nap_block,
    build_scenario_keyword_blocks,
)
from .summary.intelligence import normalize_observation
from .validation.evaluator import ValidationEvaluator


def build_evidence_items(data: dict[str, Any]) -> list[EvidenceItem]:
    """Normalize list or legacy category-object evidence input."""

    raw = data.get("evidence") or []
    if isinstance(raw, dict):
        result: list[EvidenceItem] = []
        global_index = 0
        for category, value in raw.items():
            if value in (None, ""):
                continue
            values = value if isinstance(value, list) else [value]
            for entry in values:
                if isinstance(entry, dict):
                    item = EvidenceItem.from_dict(entry, global_index)
                    if not item.category or item.category == "evidence":
                        item.category = str(category).lower()
                    result.append(item)
                elif str(entry or "").strip():
                    result.append(
                        EvidenceItem(
                            id=f"E{global_index + 1:03d}",
                            claim=str(entry).strip(),
                            category=str(category).lower(),
                            status=FACT,
                            source="用户提供资料",
                            source_type="user_provided",
                        )
                    )
                global_index += 1
        return result

    items: list[EvidenceItem] = []
    for index, entry in enumerate(raw or []):
        if isinstance(entry, str):
            text = entry.strip()
            if text:
                items.append(
                    EvidenceItem(
                        id=f"E{index + 1:03d}",
                        claim=text,
                        status=FACT if text.upper() != UNKNOWN else UNKNOWN,
                        source="用户提供资料" if text.upper() != UNKNOWN else "",
                        source_type="user_provided" if text.upper() != UNKNOWN else "unknown",
                    )
                )
        else:
            items.append(EvidenceItem.from_dict(entry, index))
    return items


class DiagnosticPipeline:
    def __init__(self, offline: bool = True, research_mode: str = "offline") -> None:
        self.offline = offline
        self.research_mode = research_mode if research_mode in {"manual", "provided", "external", "offline"} else "offline"
        self.provider: ResearchProvider = OfflineProvider() if offline else ManualProvider()

    def run(self, data: dict[str, Any]) -> dict[str, Any]:
        company = CompanyProfile.from_dict(data)
        entity = EntityResearcher(mode=self.research_mode).research(company)
        observations = CognitionAnalyzer.observations_from_input(data, company)

        matrix = QueryMatrix().build(company)
        coverage = matrix.coverage(observations)
        cognition = CognitionAnalyzer(company, entity).analyze(observations, matrix)

        evidence_items = build_evidence_items(data)
        company_name = entity.get_value("name")
        for item in evidence_items:
            item.entity_match = bool(item.entity) and item.entity == company_name
            item.verifiable = item.source_type in {
                "official",
                "government",
                "third_party",
                "media",
            }
        graph = build_evidence_graph(entity, evidence_items)
        evidence_result = EvidenceVerifier().verify(evidence_items)
        eeaap = EeaapScorer().score(entity, evidence_items, evidence_result.score)
        eeat = EeatScorer().score(entity, evidence_items, evidence_result, eeaap)

        client_scores = {
            "entity": entity_score_from_entity(entity),
            "evidence": evidence_result.score,
            "authority": eeat.get("authoritativeness", 0),
            "citation": coverage.citation_rate if coverage.citation_rate is not None else None,
            "recommendation": coverage.recommendation_rate if coverage.recommendation_rate is not None else None,
        }
        competitors = CompetitorAnalyzer(company.name).analyze(
            [Competitor.from_dict(item) for item in data.get("competitors") or []],
            entity,
            client_scores,
            matrix,
        )
        gaps = analyze_gaps(
            entity,
            evidence_result,
            eeaap,
            eeat,
            coverage,
            matrix,
            competitors.status,
            competitors.score,
            company.issues,
        )
        opportunities = OpportunityScorer().score(
            gaps["gaps"],
            matrix.queries,
            company.current_metrics,
        )
        recommendations = RecommendationPlanner().plan(gaps["gaps"], opportunities["opportunities"])
        validation = self._validation(company, recommendations)
        quality = compute_data_quality(entity, evidence_items, observations, matrix.queries)
        provisional = {
            "query_matrix": matrix.to_dict(coverage),
            "ai_cognition": {
                **cognition,
                "query_bank": build_cognition_queries(company, entity),
            },
            "company": {
                "name": company.name or entity.get_value("name"),
                "business": company.business or entity.get_value("business"),
                "industry": company.industry or entity.get_values("industry"),
                "customers": company.customers or entity.get_values("customers"),
                "locations": company.locations or entity.get_values("locations"),
                "aliases": company.aliases or entity.get_values("aliases"),
                "issues": company.issues,
                "raw": data.get("company") or {},
            },
            "entity": entity.to_dict(),
        }
        scenarios = build_scenario_keyword_blocks(provisional)
        citations = build_citation_block(provisional)
        nap = build_nap_block(provisional)
        ai_tests = analyze_ai_tests(
            [
                normalize_observation(item.to_dict())
                for item in observations
                if item.observation_mode in {"observed", "provided"}
            ]
        )
        ai_tests["basis"] = "只统计真实 AI 测试结果；模拟或未知记录不计分。" if ai_tests["total"] else (
            "没有真实 AI 测试结果；Mention/Recommendation/Citation 保持 NOT_RUN，不计算数字。"
        )

        scorecard = build_scorecard(
            entity,
            cognition,
            coverage,
            evidence_result,
            eeaap,
            eeat,
            competitors.score,
            quality["score"],
            scenarios=scenarios,
            citations=citations,
            nap=nap,
        )

        result = DiagnosticResult(
            meta={
                "engine": "GEO Diagnostic Engine",
                "version": __version__,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "offline": self.offline,
                "research_mode": self.research_mode,
                "diagnostic_note": "Score is a diagnostic indicator, not a ranking guarantee.",
            },
            company=provisional["company"],
            entity=entity.to_dict(),
            ai_cognition=provisional["ai_cognition"],
            query_matrix=matrix.to_dict(coverage),
            competitors=competitors.to_dict(),
            evidence_graph=graph.to_dict(),
            eeaap=eeaap,
            eeat=eeat,
            gaps=gaps,
            opportunities=opportunities,
            recommendations=recommendations,
            validation=validation,
            scores=scorecard.to_dict(),
            data_quality=quality,
            scenarios=scenarios,
            keywords={
                "status": scenarios["keyword_status"],
                "coverage": scenarios["keyword_coverage"],
                "keyword_coverage_score": scenarios["keyword_coverage_score"],
                "keywords": scenarios["keywords"],
                "basis": scenarios["basis"],
            },
            citations=citations,
            nap=nap,
            ai_tests=ai_tests,
        )
        result.competition_intelligence = build_competition_intelligence(result.to_dict())
        return result.to_dict()

    def _validation(self, company: CompanyProfile, recommendations: dict[str, Any]) -> dict[str, Any]:
        before = company.current_metrics
        after = company.validation.get("after_metrics") or {}
        evaluator = ValidationEvaluator().evaluate(before, after)
        first_action = (recommendations.get("actions") or [{}])[0]
        return {
            **evaluator,
            "plan": {
                "status": "READY",
                "steps": [
                    "记录同一批 Query 的 AI 观察结果作为 After 基线",
                    "优先验证 P0 动作对应的电话/官网露出与推荐率",
                    "首次复测建议在发布成功 20 篇后间隔 7-15 天；再次复测间隔 7 天",
                    "复测结论必须是真实观察，不能把预期写成结果",
                ],
                "first_p0_verification": first_action.get("verification", "尚未生成 P0 动作。"),
            },
            "before_metrics": before,
            "after_metrics": after,
        }


def entity_score_from_entity(entity: Any) -> int:
    from .scorecard import entity_score

    return entity_score(entity)
