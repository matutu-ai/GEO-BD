"""Summarize the current AI diagnosis without running another analysis pass."""

from __future__ import annotations

from typing import Any


UNKNOWN = "【需客户补充真实资料】"
REAL_MODES = {"observed", "provided"}


class DiagnosisAgent:
    """Create a compact, evidence-bounded diagnosis handoff."""

    def build(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        observations = _real_observations(diagnostic)
        return {
            "company_position": _company_position(diagnostic),
            "public_information_status": _public_information_status(diagnostic),
            "ai_cognition_status": _ai_cognition_status(observations),
            "core_problems": _core_problems(diagnostic, observations),
            "current_stage": _current_stage(diagnostic, observations),
        }


def render_diagnosis_summary(summary: dict[str, Any]) -> str:
    """Render the diagnosis as a short operator-facing Markdown handoff."""

    problems = summary.get("core_problems") or [UNKNOWN]
    lines = [
        "# AI诊断总结",
        "",
        f"## 企业当前定位\n\n{_text(summary.get('company_position'))}",
        "",
        f"## 对外公开状态\n\n{_text(summary.get('public_information_status'))}",
        "",
        f"## AI当前认知\n\n{_text(summary.get('ai_cognition_status'))}",
        "",
        "## 当前核心问题",
        "",
        *[f"- {item}" for item in problems],
        "",
        f"## 当前阶段\n\n{_text(summary.get('current_stage'))}",
        "",
    ]
    return "\n".join(lines)


def _company_position(diagnostic: dict[str, Any]) -> str:
    company = diagnostic.get("company") or {}
    entity = diagnostic.get("entity") or {}
    business = str(company.get("business") or _entity_value(entity, "business") or "").strip()
    text = " ".join(
        [business, *_values(company.get("products")), *_entity_values(entity, "products")]
    )
    if "通风" in text:
        return "人防通风系统供应商"
    return business or UNKNOWN


def _public_information_status(diagnostic: dict[str, Any]) -> str:
    company = diagnostic.get("company") or {}
    entity = diagnostic.get("entity") or {}
    if not company.get("name") and not _entity_value(entity, "name"):
        return f"{UNKNOWN} 当前没有足够企业资料判断对外公开状态。"
    known_fields = sum(bool(company.get(key) or _entity_values(entity, key)) for key in (
        "business", "industry", "products", "services", "customers", "locations"
    ))
    missing = [str(item) for item in entity.get("missing") or []]
    if missing:
        return f"企业已有 {known_fields} 类基础公开信息，但仍缺少 {', '.join(missing[:5])} 等字段，公开信息体系尚不完整。"
    return "企业已有基础公开信息；来源一致性和资料时效仍需逐项核验。"


def _ai_cognition_status(observations: list[dict[str, Any]]) -> str:
    if not observations:
        return f"{UNKNOWN} 当前没有 observed/provided 的真实 AI 观察，不能判断企业是否已被 AI 识别或推荐。"
    mentioned = _rate(observations, "company_mentioned")
    recommended = _rate(observations, "company_recommended")
    cited = _rate(observations, "company_cited")
    if mentioned > 0 and recommended < mentioned:
        return f"AI可以识别企业存在（提及率 {mentioned}%），但尚未形成稳定的专业推荐认知（推荐率 {recommended}%）；引用率为 {cited}%。"
    return f"AI已在真实观察中识别企业（提及率 {mentioned}%），推荐率为 {recommended}%，引用率为 {cited}%；仍需继续核验认知稳定性。"


def _core_problems(diagnostic: dict[str, Any], observations: list[dict[str, Any]]) -> list[str]:
    tasks = (diagnostic.get("optimization_tasks") or {}).get("tasks") or []
    labels = {
        "企业定位校准任务": "企业定位不够明确",
        "企业信息资产补充任务": "企业信息资产不足",
        "专业内容建设任务": "专业能力表达不足",
        "信任信息增强任务": "信任信息不足",
    }
    problems = [labels[task["title"]] for task in tasks if task.get("title") in labels]
    if not observations and UNKNOWN not in problems:
        problems.insert(0, f"{UNKNOWN} AI认知表现尚未完成真实测试")
    return problems or [f"{UNKNOWN} 当前诊断没有可归纳的核心问题。"]


def _current_stage(diagnostic: dict[str, Any], observations: list[dict[str, Any]]) -> str:
    company = diagnostic.get("company") or {}
    if not company.get("name") and not (diagnostic.get("entity") or {}).get("fields"):
        return "企业资料补齐阶段"
    if not observations:
        return "AI认知待测阶段"
    return "AI认知建立阶段"


def _real_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    observations = (diagnostic.get("ai_cognition") or {}).get("observations") or []
    return [
        item for item in observations
        if str(item.get("status") or item.get("observation_mode") or "").lower() in REAL_MODES
    ]


def _rate(observations: list[dict[str, Any]], field: str) -> int:
    return round(100 * sum(bool(item.get(field)) for item in observations) / len(observations))


def _entity_value(entity: dict[str, Any], key: str) -> str:
    return (_entity_values(entity, key) or [""])[0]


def _entity_values(entity: dict[str, Any], key: str) -> list[str]:
    return [
        str(item.get("value"))
        for item in (entity.get("fields") or {}).get(key) or []
        if item.get("value") and str(item.get("value")).upper() != "UNKNOWN"
    ]


def _values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if value else []


def _text(value: Any) -> str:
    return str(value or UNKNOWN)
