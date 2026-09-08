"""Deterministic enterprise intelligence and conditional recommendation engine.

The engine never invents evidence or qualifications. Every recommendation is
derived from entity/evidence inputs; product keyword presence alone never
upgrades a regulated qualification from unverified/unknown to verified.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..common import clamp, has_exaggeration, is_unknown
from .constants import (
    BAND_LABELS,
    CLAIM_SAFETY_STATUSES,
    MARKETING_CLAIM_PATTERNS,
    QUALIFICATION_MATCH,
    SOURCE_STRENGTH,
    TIER_SOURCE_TYPES,
    recommendation_band,
)
from .models import (
    Capability,
    ClaimSafety,
    CompanyIntelligence,
    CompetitionIntelligence,
    CompetitorPool,
    CustomerScenario,
    EvidenceReview,
    GeoContentGap,
    Positioning,
    PromotionStrategy,
    QualificationBoundary,
    RecommendationDecision,
)


REGION_ALIASES = OrderedDict(
    [
        ("北京", ("北京", "京津冀")),
        ("上海", ("上海", "长三角")),
        ("江苏", ("江苏", "苏州", "无锡", "南京", "长三角")),
        ("浙江", ("浙江", "杭州", "宁波", "长三角")),
        ("安徽", ("安徽", "合肥", "长三角")),
        ("广东", ("广东", "深圳", "广州", "东莞", "佛山", "珠三角")),
        ("山东", ("山东", "济南", "青岛", "德州", "烟台", "潍坊")),
        ("河南", ("河南", "郑州", "洛阳", "新乡", "安阳", "开封")),
        ("河北", ("河北", "石家庄", "保定", "唐山")),
        ("四川", ("四川", "成都")),
        ("湖北", ("湖北", "武汉")),
        ("湖南", ("湖南", "长沙")),
        ("福建", ("福建", "厦门", "福州")),
        ("陕西", ("陕西", "西安")),
        ("山西", ("山西", "太原")),
        ("辽宁", ("辽宁", "沈阳", "大连")),
        ("天津", ("天津", "京津冀")),
        ("重庆", ("重庆", "成渝")),
        ("云南", ("云南", "昆明")),
        ("贵州", ("贵州", "贵阳")),
        ("江西", ("江西", "南昌")),
        ("广西", ("广西", "南宁")),
        ("新疆", ("新疆", "乌鲁木齐")),
        ("甘肃", ("甘肃", "兰州")),
        ("内蒙古", ("内蒙古", "呼和浩特")),
        ("海南", ("海南", "海口")),
        ("吉林", ("吉林", "长春")),
        ("黑龙江", ("黑龙江", "哈尔滨")),
        ("宁夏", ("宁夏", "银川")),
        ("青海", ("青海", "西宁")),
        ("西藏", ("西藏", "拉萨")),
        ("香港", ("香港",)),
        ("澳门", ("澳门",)),
        ("台湾", ("台湾",)),
    ]
)

PRODUCT_CATALOG = {
    "通风设备": ("通风设备", "人防通风", "通风机", "滤尘", "空气处理", "消声器", "风管", "风机"),
    "过滤吸收器": ("过滤吸收器", "滤毒", "过滤", "吸收器"),
    "油网滤尘器": ("油网滤尘器", "滤尘器", "油网"),
    "密闭阀门": ("密闭阀", "密闭阀门", "气密阀", "防爆波阀", "排气活门"),
    "人防门": ("人防门", "防护门", "密闭门", "防爆波活门"),
    "人防工程配套": ("人防", "人防工程", "防空地下室", "防护设备"),
    "系统集成": ("系统集成", "通风系统", "整体配套", "安装调试", "成套"),
    "非标定制": ("非标", "定制", "异形"),
}

PRODUCT_TERM_PATTERNS = {
    "设备": ("设备", "机组", "装置"),
    "阀门": ("阀", "活门"),
    "门": ("门",),
    "过滤器": ("过滤吸收器", "滤尘器", "过滤器"),
    "风机": ("风机", "通风机"),
    "控制柜": ("控制柜", "控制箱"),
}

QUALIFICATION_TERMS = {
    "人防门定点生产": ("人防门定点生产资质", "人防门定点生产厂家", "人防门定点生产企业"),
    "人防防护设备定点生产": ("防护设备定点生产", "人防防护设备生产资质"),
    "人防工程防护设备生产安装": ("人防工程防护设备", "防护设备生产安装", "人防设备生产资质"),
    "消防工程资质": ("消防设施工程", "消防资质"),
    "机电安装资质": ("建筑机电安装", "机电安装资质", "机电工程施工"),
    "特种设备生产许可": ("特种设备生产许可", "压力容器制造", "锅炉制造"),
    "生产许可": ("生产许可", "生产许可证", "生产资质", "制造许可"),
}

QUALIFIER_REQUIRED_WORDS = ("定点", "生产许可", "定点生产", "生产资质", "制造许可")

SYSTEM_CAPABILITY_WORDS = ("系统集成", "系统配套", "成套", "整体方案", "安装调试", "工程")
SERVICE_CAPABILITY_WORDS = ("维保", "售后", "服务", "培训")
OEM_CAPABILITY_WORDS = ("代工", "OEM", "贴牌", "委托加工")
CUSTOM_CAPABILITY_WORDS = ("非标", "定制", "特殊规格")
DELIVERY_CAPABILITY_WORDS = ("安装", "交付", "物流", "供货")
PROJECT_CAPABILITY_WORDS = ("项目", "工程", "施工")
TECHNICAL_CAPABILITY_WORDS = ("研发", "设计", "技术", "工艺")
MANUFACTURE_WORDS = ("设备", "机", "阀", "门", "器", "生产", "制造")
MANUFACTURED_PRODUCT_HINTS = ("厂", "生产", "制造", "实业")

QUALIFICATION_PATTERNS = (
    "资质",
    "许可",
    "定点生产",
    "定点企业",
    "入网",
    "名录",
    "备案",
    "认证",
    "检测报告",
)

REGULATED_PRODUCT_TERMS = {
    "人防门": "人防门定点生产",
    "防护门": "人防门定点生产",
    "人防防护设备": "人防防护设备定点生产",
    "防护设备": "人防防护设备定点生产",
}

SEARCH_CUSTOMER_TYPES = {
    "终端": "终端客户",
    "采购": "采购商",
    "开发商": "房地产开发商",
    "总包": "总包",
    "工程公司": "工程公司",
    "施工": "工程公司",
    "设计院": "设计院",
    "渠道": "渠道商",
    "分销": "代理商",
    "代理": "代理商",
    "OEM": "OEM客户",
    "政府": "政府/事业单位",
    "事业单位": "政府/事业单位",
    "医院": "政府/事业单位",
    "学校": "政府/事业单位",
}


@dataclass
class EnterpriseKnowledge:
    company_name: str = ""
    products: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    business: str = ""
    company_raw: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    customers: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    cases: list[str] = field(default_factory=list)
    certificates: list[str] = field(default_factory=list)
    ai_observations: list[dict[str, Any]] = field(default_factory=list)

    @property
    def company_text(self) -> str:
        return " ".join(
            [
                self.company_name,
                self.business,
                " ".join(self.products),
                " ".join(self.services),
                " ".join(self.cases),
                " ".join(self.certificates),
            ]
        )


def build_competition_intelligence(diagnostic: dict[str, Any]) -> dict[str, Any]:
    """Build the top-level competition_intelligence block from a DiagnosticResult."""
    knowledge = _extract_knowledge(diagnostic)
    if not knowledge.company_name:
        return CompetitionIntelligence(
            recommendation_status="UNKNOWN",
            basis="缺少企业名称与基础资料，无法进行企业背调与条件式推荐。",
        ).to_dict()

    capability_map = _build_capabilities(knowledge)
    boundary = _build_qualification_boundary(knowledge)
    reviews = _build_evidence_reviews(knowledge)

    product_catalog = _product_catalog(knowledge)
    company_regions = _detected_regions(knowledge.company_text, knowledge.locations)
    scenarios = _build_scenarios(knowledge, product_catalog, company_regions, boundary, reviews)
    recommended_rows, conditional_rows, restricted_rows = _scenario_splits(scenarios)

    ai_factor = _ai_perception_factor(knowledge)
    decisions = _recommendation_decisions(
        diagnostic,
        knowledge,
        product_catalog,
        company_regions,
        boundary,
        reviews,
        ai_factor,
    )
    pools = _competitor_pools(diagnostic, knowledge)
    positioning = _positioning(
        knowledge,
        product_catalog,
        company_regions,
        scenarios,
        boundary,
        decisions,
    )
    promotion = _promotion_strategy(knowledge, capability_map, boundary, company_regions)
    claims = _claim_safety(knowledge, boundary)
    gaps = _geo_content_gaps(knowledge, capability_map, boundary, company_regions, scenarios)
    intelligence = _company_intelligence(knowledge, capability_map, boundary, company_regions)

    return CompetitionIntelligence(
        company_intelligence=intelligence,
        capabilities=sorted(capability_map.values(), key=lambda item: (-item.level, item.type, item.capability)),
        qualification_boundary=boundary,
        evidence_review=reviews,
        competitor_pools=pools,
        customer_scenarios=scenarios,
        recommendation_decisions=decisions,
        positioning=positioning,
        promotion_strategy=promotion,
        geo_content_gaps=gaps,
        claim_safety=claims,
        recommendation_status="COMPUTED",
        basis=(
            "企业背调与推荐仅基于输入资料与可追溯证据；资质判断必须绑定来源，"
            "产品关键词不会自动升级为资质。离线模式不联网核验，推荐为资料级匹配，不是资质担保。"
        ),
    ).to_dict()


def _extract_knowledge(diagnostic: dict[str, Any]) -> EnterpriseKnowledge:
    company = diagnostic.get("company") or {}
    entity = diagnostic.get("entity") or {}
    fields = entity.get("fields") or {}

    def values(key: str) -> list[str]:
        return [str(item.get("value") or "").strip() for item in fields.get(key) or [] if item.get("value") and not is_unknown(item.get("value"))]

    raw_company = company.get("raw") or diagnostic.get("company") or {}
    if not isinstance(raw_company, dict):
        raw_company = {}
    products = _dedupe(values("products") or _string_list(raw_company.get("products")))
    services = _dedupe(values("services") or _string_list(raw_company.get("services")))
    name = values("name") or [str(company.get("name") or raw_company.get("name") or "").strip()]
    certificates = _dedupe(values("certificates") or _string_list(raw_company.get("certificates")))
    customers = _dedupe(values("customers") or _string_list(raw_company.get("customers")))
    locations = _dedupe(values("locations") or _string_list(raw_company.get("locations")))
    return EnterpriseKnowledge(
        company_name=name[0] if name and name[0] else "",
        products=products,
        services=services,
        business=str(raw_company.get("business") or values("business") or "").strip(),
        company_raw=raw_company,
        evidence=_evidence_items(diagnostic),
        customers=customers,
        locations=locations,
        cases=_string_list(raw_company.get("cases")) + _string_list(values("cases")),
        certificates=certificates,
        ai_observations=_real_observations(diagnostic),
    )


def _evidence_items(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return list((diagnostic.get("evidence_graph") or {}).get("items") or [])


def _real_observations(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in (diagnostic.get("ai_cognition") or {}).get("observations") or []:
        mode = str(item.get("status") or item.get("observation_mode") or "")
        if mode in {"observed", "provided"}:
            result.append(item)
    return result


def _company_intelligence(
    knowledge: EnterpriseKnowledge,
    capabilities: dict[str, Capability],
    boundary: list[QualificationBoundary],
    regions: list[str],
) -> CompanyIntelligence:
    raw = knowledge.company_raw
    all_text = knowledge.company_text
    products = _dedupe(knowledge.products)
    services = _dedupe(knowledge.services)
    unknown = []
    for label, value in (
        ("成立时间/注册年份", raw.get("founded_year")),
        ("注册资本", raw.get("registered_capital")),
        ("法定代表人", raw.get("legal_representative")),
        ("股东/股权结构", raw.get("shareholders")),
        ("工商处罚/经营异常", raw.get("negative_information") if not raw.get("negative_information") else None),
    ):
        if value in (None, "", [], {}, "UNKNOWN", "未知"):
            unknown.append(label)

    derived_manufacturing = [item.capability for item in capabilities.values() if item.type == "MANUFACTURING"]
    derived_technical = [item.capability for item in capabilities.values() if item.type == "TECHNICAL"]
    scenario_hints = _detected_scenarios(services, all_text)
    region_hints = _detected_regions(all_text, knowledge.locations)
    constraint_hints = [item.item for item in boundary if item.status in {"unverified", "absent", "partner_required", "unknown"}]
    business_model = [str(raw.get("business") or "").strip(), "制造与配套" if derived_manufacturing else "", "工程与服务" if services else ""]
    business_model = [item for item in business_model if item]
    primary = knowledge.business or "、".join(products[:3]) if products else knowledge.business
    secondary = [item for item in services if item and item not in ([""] + products)]
    return CompanyIntelligence(
        company_name=knowledge.company_name,
        legal_name=str(raw.get("legal_name") or raw.get("legalName") or knowledge.company_name).strip(),
        location=str(raw.get("location") or "、".join(knowledge.locations)).strip(),
        founded_year=raw.get("founded_year"),
        registered_capital=raw.get("registered_capital"),
        industry=_string_list(raw.get("industry")),
        business_model=business_model,
        primary_business=[primary] if primary else [],
        secondary_business=secondary[:10],
        products=products,
        services=services,
        target_customers=knowledge.customers,
        target_regions=region_hints,
        application_scenarios=scenario_hints,
        manufacturing_capabilities=derived_manufacturing,
        technology_capabilities=derived_technical,
        project_experience=knowledge.cases,
        brand_attributes=_string_list(raw.get("brands")) + _string_list(raw.get("media")),
        known_constraints=constraint_hints,
        unknown_items=_dedupe(unknown),
    )


def _build_capabilities(knowledge: EnterpriseKnowledge) -> dict[str, Capability]:
    all_text = knowledge.company_text
    products = knowledge.products
    services = knowledge.services
    capabilities: OrderedDict[str, Capability] = OrderedDict()

    def evidence_ids_for(terms: Iterable[str]) -> list[str]:
        matched: list[str] = []
        for item in knowledge.evidence:
            claim = str(item.get("claim") or "")
            if claim and any(term.lower() in claim.lower() for term in terms):
                matched.append(str(item.get("id") or ""))
        return matched

    for product in products:
        level = 45 + 25 * int(bool(evidence_ids_for([product])))
        cap_type = "PRODUCT"
        if any(term in product for term in MANUFACTURED_PRODUCT_HINTS) or any(term in product for term in ("阀", "门", "机", "器")):
            cap_type = "MANUFACTURING"
        capability = f"{product}生产/供货" if cap_type == "MANUFACTURING" else f"{product}产品"
        capabilities[capability] = Capability(
            capability=capability,
            type=cap_type,
            level=clamp(level),
            evidence=evidence_ids_for([product]),
            confidence=75 if evidence_ids_for([product]) else 60,
            regions=[],
            scenarios=[product],
            limitations=[],
        )

    service_labels = (
        ("SYSTEM_INTEGRATION", SYSTEM_CAPABILITY_WORDS, "通风/机电系统集成与配套"),
        ("SERVICE", SERVICE_CAPABILITY_WORDS, "安装维保与售后服务"),
        ("OEM", OEM_CAPABILITY_WORDS, "OEM/代加工服务"),
        ("CUSTOMIZATION", CUSTOM_CAPABILITY_WORDS, "非标定制服务"),
        ("DELIVERY", DELIVERY_CAPABILITY_WORDS, "工程交付与供货"),
        ("PROJECT", PROJECT_CAPABILITY_WORDS, "工程项目实施"),
        ("TECHNICAL", TECHNICAL_CAPABILITY_WORDS, "设计研发与技术能力"),
    )
    for cap_type, words, label in service_labels:
        matched = [service for service in services if any(word.lower() in service.lower() for word in words)]
        if not matched:
            continue
        evidence = evidence_ids_for(matched)
        capabilities[label] = Capability(
            capability=label,
            type=cap_type,
            level=clamp(60 + 20 * int(bool(evidence))),
            evidence=evidence,
            confidence=75 if evidence else 65,
            regions=[],
            scenarios=matched[:6],
            limitations=[],
        )

    if any(term in all_text for term in MANUFACTURE_WORDS) and not any(item.type == "MANUFACTURING" for item in capabilities.values()):
        capabilities["生产制造能力"] = Capability(
            capability="生产制造能力",
            type="MANUFACTURING",
            level=50,
            evidence=[],
            confidence=55,
            regions=[],
            scenarios=[],
            limitations=["尚无具体生产参数或产线证据，需要补充检测报告/工艺文件后再提级。"],
        )
    return dict(capabilities)


def _build_qualification_boundary(knowledge: EnterpriseKnowledge) -> list[QualificationBoundary]:
    result: list[QualificationBoundary] = []
    seen: set[str] = set()
    certificates = [text for text in knowledge.certificates if text]
    claims = [str(item.get("claim") or "").strip() for item in knowledge.evidence if str(item.get("claim") or "").strip()]
    all_text = knowledge.company_text + " " + " ".join(claims)

    def add_qualification(item: str, qual_type: str = "qualification") -> None:
        key = item.lower()
        if key in seen or not item:
            return
        seen.add(key)
        evidence = [
            str(evidence_item.get("id") or "")
            for evidence_item in knowledge.evidence
            if str(evidence_item.get("claim") or "").lower().find(item.lower()) >= 0
        ]
        verified = any(
            item.lower() in str(evidence_item.get("claim") or "").lower()
            and bool(evidence_item.get("verified"))
            and str(evidence_item.get("source_type") or "") in {"official", "government", "user_provided"}
            for evidence_item in knowledge.evidence
        )
        absent = any(
            item.lower() in str(evidence_item.get("claim") or "").lower()
            and any(word in str(evidence_item.get("claim") or "") for word in ("未取得", "未具备", "未通过", "没有", "不代表", "不是", "并非", "无"))
            for evidence_item in knowledge.evidence
        )
        status = "absent" if absent and not verified else "verified" if verified else "unverified"
        allowed = [f"已提供{item}材料" if item in certificates else f"企业可公开说明与{item}有关的经营情况"]
        forbidden = [f"企业已通过{QUALIFICATION_PATTERNS[0]}审批/具备{item}"]
        result.append(
            QualificationBoundary(
                item=item,
                type=qual_type,
                status=status,
                evidence=evidence,
                risk_level="low" if verified else "medium" if absent else "high",
                allowed_claims=allowed,
                forbidden_claims=forbidden,
                recommended_disclosure=(
                    f"可核验来源：{item}（附证据编号 {'/'.join(evidence) if evidence else '待补充'}）"
                    if verified
                    else f"来源明确说明未取得{item}；不可宣传为具备。"
                    if absent
                    else f"{item}尚未完成独立核验；在取得官方来源前，不建议宣传为已具备。"
                ),
            )
        )

    for certificate in certificates:
        add_qualification(certificate)

    for claim in claims:
        for pattern in QUALIFICATION_PATTERNS:
            if pattern in claim.lower():
                phrases = _extract_qualification_phrases(claim)
                for phrase in phrases:
                    add_qualification(phrase, "regulatory" if any(word in phrase for word in ("许可", "定点", "备案", "资质")) else "qualification")

    return result


def _extract_qualification_phrases(claim: str) -> list[str]:
    phrases: list[str] = []
    for match in re.finditer(r"([\u4e00-\u9fffA-Za-z0-9]{2,20}(?:资质|许可证|定点生产|定点企业|入网|备案|认证))", claim):
        phrase = _clean_qualification_phrase(match.group(1))
        if phrase and phrase not in phrases:
            phrases.append(phrase)
    return phrases[:5]


def _clean_qualification_phrase(phrase: str) -> str:
    stripped = phrase.lstrip("无")
    if stripped != phrase:
        phrase = stripped
    for negative in ("未取得", "未具备", "未通过", "未持有", "未拥有", "不代表", "不具备", "没有", "并非", "不是"):
        index = phrase.find(negative)
        if index >= 0:
            phrase = phrase[index + len(negative):]
            break
    for head in ("已取得", "未取得", "取得", "已具备", "未具备", "具备", "已持有", "未持有", "持有", "已拥有", "未拥有", "拥有", "已通过", "未通过", "通过", "获颁", "获授"):
        index = phrase.rfind(head)
        if index >= 0:
            phrase = phrase[index + len(head):]
            break
    phrase = re.sub(r"(证书复印件|复印件|材料|证明|文件|原件|扫描件|审查|审批)$", "", phrase)
    return phrase.strip()


def _build_evidence_reviews(knowledge: EnterpriseKnowledge) -> list[EvidenceReview]:
    reviews: list[EvidenceReview] = []
    items = knowledge.evidence
    by_id = {str(item.get("id") or ""): item for item in items}
    for item in items:
        item_id = str(item.get("id") or "")
        claim = str(item.get("claim") or "")
        source_type = str(item.get("source_type") or "unknown")
        tier = TIER_SOURCE_TYPES.get(source_type, 5)
        source_factor = SOURCE_STRENGTH.get(source_type, 0.1)
        verified = bool(item.get("verified"))
        conflicts = [str(value) for value in item.get("conflicts_with") or []]
        supports, contradicts = [], []
        for value in conflicts:
            contradicts.append(value)
        strength = clamp(100 * (0.6 * source_factor + 0.4 * (1.0 if verified else 0.3)))
        verification = "verified" if verified else "conflict" if conflicts else "unverified"
        if not str(item.get("source") or "").strip():
            verification = "unknown"
        supports = [other_id for other_id in by_id if _supports(other_id, item_id, by_id)]
        contradicts = [other_id for other_id in by_id if _contradicts(other_id, item_id, by_id, conflicts)]
        reviews.append(
            EvidenceReview(
                id=item_id,
                claim=claim,
                source=str(item.get("source") or ""),
                source_type=source_type,
                tier=tier,
                date=str(item.get("date") or ""),
                region=str(item.get("region") or ""),
                evidence_strength=strength,
                verification_status=verification,
                supports=supports,
                contradicts=contradicts,
            )
        )
    return reviews


def _supports(other_id: str, item_id: str, by_id: dict[str, dict[str, Any]]) -> bool:
    if other_id == item_id:
        return False
    other = by_id.get(other_id)
    item = by_id.get(item_id)
    if not other or not item:
        return False
    other_claim = str(other.get("claim") or "")
    item_claim = str(item.get("claim") or "")
    shared = [term for term in (other_claim + item_claim).split() if len(term) >= 4]
    return bool(shared) and (other_claim in item_claim or item_claim in other_claim or any(term in other_claim for term in _keywords(item_claim)))


def _contradicts(other_id: str, item_id: str, by_id: dict[str, dict[str, Any]], conflicts: list[str]) -> bool:
    return other_id != item_id and (other_id in conflicts)


def _keywords(text: str) -> list[str]:
    return [part for part in re.split(r"[\s，。、；：,.;:()（）/]+", text) if len(part) >= 2 and not part.isdigit()][:10]


def _detected_scenarios(services: list[str], text: str) -> list[str]:
    result: list[str] = []
    for service in services:
        if any(word in service for word in ("安装", "调试", "维保", "售后")):
            result.append(f"{service}场景")
    for term in ("人防工程", "通风工程", "项目配套", "改造", "新建"):
        if term in text and not any(term in item for item in result):
            result.append(f"{term}配套")
    return _dedupe(result)[:12]


def _detected_regions(text: str, locations: list[str]) -> list[str]:
    result: list[str] = []
    combined = " ".join(locations) + " " + text
    for region, aliases in REGION_ALIASES.items():
        if any(alias in combined for alias in aliases) and region not in result:
            result.append(region)
    return result


def _product_catalog(knowledge: EnterpriseKnowledge) -> list[str]:
    """Return catalog entries whose terms actually appear in company input."""
    catalog: list[str] = []
    text = (knowledge.company_text + " " + " ".join(knowledge.products)).lower()
    for product, synonyms in PRODUCT_CATALOG.items():
        terms = (product,) + synonyms
        if any(term.lower() in text for term in terms):
            catalog.append(product)
    for product in knowledge.products:
        if product and product not in catalog:
            catalog.append(product)
    return catalog


def _ai_perception_factor(knowledge: EnterpriseKnowledge) -> float:
    observations = knowledge.ai_observations
    if not observations:
        return 1.0
    recommended = sum(1 for item in observations if item.get("company_recommended"))
    mentioned = sum(1 for item in observations if item.get("company_mentioned"))
    denominator = max(len(observations), 1)
    factor = 0.6 + 0.4 * (0.6 * recommended / denominator + 0.4 * mentioned / denominator)
    return min(1.0, max(0.0, factor))


def _evidence_score_for(knowledge: EnterpriseKnowledge, terms: Iterable[str]) -> int:
    terms = [term.lower() for term in terms if term]
    matched = [
        item
        for item in knowledge.evidence
        if str(item.get("claim") or "").lower() and any(term in str(item.get("claim") or "").lower() for term in terms)
    ]
    if not matched:
        return 35
    verified = sum(1 for item in matched if item.get("verified"))
    return clamp(50 + 50 * (verified / len(matched)))


def _qualification_status_for(boundary: list[QualificationBoundary], terms: Iterable[str]) -> str:
    lowered = [term.lower() for term in terms if term]
    if not lowered:
        return "unknown"
    for item in boundary:
        item_lower = item.item.lower()
        if any(term in item_lower or item_lower in term for term in lowered):
            return item.status
    return "unknown"


def _qualification_status_for_boundary(
    knowledge: EnterpriseKnowledge,
    boundary: list[QualificationBoundary],
    requirement_terms: Iterable[str],
) -> str:
    """Resolve requirement terms against the boundary, never from products alone."""
    terms = [str(term).strip() for term in requirement_terms if str(term or "").strip()]
    if not terms:
        return "verified"
    status = _qualification_status_for(boundary, terms)
    if status == "unknown":
        return _unverified_status_from_input(knowledge, terms)
    return status


def _unverified_status_from_input(knowledge: EnterpriseKnowledge, terms: list[str]) -> str:
    claims_text = " ".join(
        str(item.get("claim") or "") for item in knowledge.evidence if item.get("claim")
    )
    cert_text = " ".join(knowledge.certificates)
    text = (claims_text + " " + cert_text).lower()
    if any(term.lower() in text for term in terms):
        return "verified"
    return "unverified"


def _scenario_splits(
    scenarios: list[CustomerScenario],
) -> tuple[list[CustomerScenario], list[CustomerScenario], list[CustomerScenario]]:
    recommended = [item for item in scenarios if item.recommendation_score >= 75]
    conditional = [item for item in scenarios if 60 <= item.recommendation_score < 75]
    restricted = [item for item in scenarios if item.recommendation_score < 60]
    return recommended, conditional, restricted


def _build_scenarios(
    knowledge: EnterpriseKnowledge,
    product_catalog: list[str],
    regions: list[str],
    boundary: list[QualificationBoundary],
    reviews: list[EvidenceReview],
) -> list[CustomerScenario]:
    scenarios: list[CustomerScenario] = []
    products = " ".join(knowledge.products + [knowledge.business, knowledge.company_text])
    for product in product_catalog:
        synonyms = PRODUCT_CATALOG.get(product, (product,))
        if not any(synonym in products for synonym in synonyms) and not any(synonym in knowledge.services for synonym in synonyms):
            continue
        regulated = next(
            (term for term in REGULATED_PRODUCT_TERMS if term in product or any(term in synonym for synonym in synonyms)),
            None,
        )
        requirement_terms: list[str] = []
        if regulated:
            requirement_terms = list(QUALIFICATION_TERMS.get(REGULATED_PRODUCT_TERMS[regulated], []))
        scenarios.append(
            _score_scenario(
                scenario=f"需要{product}",
                customer_type="采购商/总包",
                need=f"采购或配套{product}",
                product_match=100,
                capability=70,
                terms=list(synonyms) + (requirement_terms or [product]),
                required_qualification=bool(requirement_terms),
                requirement_terms=requirement_terms,
                region_terms=[],
                knowledge=knowledge,
                boundary=boundary,
                reviews=reviews,
            )
        )

    for region in regions:
        scenarios.append(
            _score_scenario(
                scenario=f"{region}人防/通风项目配套",
                customer_type="工程公司/总包",
                need=f"{region}区域项目设备配套与供货",
                product_match=90,
                capability=75,
                terms=["通风", "人防", "设备"],
                required_qualification=False,
                requirement_terms=[],
                region_terms=[region],
                knowledge=knowledge,
                boundary=boundary,
                reviews=reviews,
            )
        )
    return scenarios


def _score_scenario(
    *,
    scenario: str,
    customer_type: str,
    need: str,
    product_match: int,
    capability: int,
    terms: list[str],
    required_qualification: bool,
    requirement_terms: list[str],
    region_terms: list[str],
    knowledge: EnterpriseKnowledge,
    boundary: list[QualificationBoundary],
    reviews: list[EvidenceReview],
) -> CustomerScenario:
    evidence_strength = _evidence_score_for(knowledge, terms)
    qualification_match = 100
    limitations: list[str] = []
    if required_qualification:
        status = _qualification_status_for_boundary(knowledge, boundary, requirement_terms)
        qualification_match = clamp(100 * QUALIFICATION_MATCH.get(status, 0.4))
        if status != "verified":
            limitations.append("相关定点/生产资质尚未核验；只能在取得资质或合作方背书后作为首选。")
    regional_match = 100
    if region_terms:
        text = " ".join(knowledge.locations + knowledge.services + [knowledge.company_text])
        regional_match = 100 if any(term in text for term in region_terms) else 60
        if regional_match < 100:
            limitations.append(f"缺少{ '、'.join(region_terms) }区域项目证据；建议先以实际案例证明区域服务能力。")

    score = _fit_score(
        product_match / 100.0,
        capability / 100.0,
        qualification_match / 100.0,
        1.0,
        regional_match / 100.0,
        evidence_strength / 100.0,
        1.0,
    )
    recommended = score >= 75
    band = recommendation_band(score)
    reasons = []
    if product_match >= 90:
        reasons.append("产品与需求匹配")
    if qualification_match >= 90:
        reasons.append("资质条件满足")
    elif qualification_match < 60:
        reasons.append("资质条件未满足")
    if regional_match >= 90:
        reasons.append("区域匹配")
    elif regional_match < 80:
        reasons.append("区域证据不足")
    reason = "；".join(reasons) if reasons else "按产品/能力/证据综合匹配"
    return CustomerScenario(
        scenario=scenario,
        customer_type=customer_type,
        need=need,
        product_match=product_match,
        capability_match=capability,
        qualification_match=qualification_match,
        regional_match=regional_match,
        evidence_strength=evidence_strength,
        recommendation_score=score,
        recommended=recommended,
        reason=f"{band}：{reason}",
        limitations=limitations,
    )


def _fit_score(
    product: float,
    capability: float,
    qualification: float,
    scenario: float,
    regional: float,
    evidence: float,
    ai: float,
) -> int:
    factors = [product, capability, qualification, scenario, regional, evidence, ai]
    score = 1.0
    for factor in factors:
        score *= max(0.02, min(1.0, factor))
    return clamp(100 * score**0.6)


def _recommendation_decisions(
    diagnostic: dict[str, Any],
    knowledge: EnterpriseKnowledge,
    product_catalog: list[str],
    regions: list[str],
    boundary: list[QualificationBoundary],
    reviews: list[EvidenceReview],
    ai_factor: float,
) -> list[RecommendationDecision]:
    queries: list[dict[str, str]] = []
    for product in product_catalog:
        queries.append({"query": f"{product}厂家", "intent": "采购/选型"})
    if any(word in " ".join(knowledge.services + [knowledge.company_text]) for word in SYSTEM_CAPABILITY_WORDS):
        queries.append({"query": "通风/机电系统集成商", "intent": "系统集成采购"})
    if knowledge.cases:
        queries.append({"query": "有项目案例的人防通风设备厂家", "intent": "项目采购"})
    for region in regions:
        queries.append({"query": f"{region}人防/通风项目设备厂家", "intent": "区域项目采购"})
    queries.append({"query": "人防工程通风设备供应商", "intent": "渠道/工程询价"})
    matrix_queries = list((diagnostic.get("query_matrix") or {}).get("queries") or [])
    for item in matrix_queries:
        query_text = str(item.get("query") or "").strip()
        if query_text:
            queries.append({"query": query_text, "intent": str(item.get("intent") or "用户侧诊断 Query")})

    unique_queries: OrderedDict[str, str] = OrderedDict()
    for item in queries:
        if item["query"] and item["query"] not in unique_queries:
            unique_queries[item["query"]] = item["intent"]

    decisions: list[RecommendationDecision] = []
    for query, intent in unique_queries.items():
        decisions.append(
            _score_query_decision(
                query,
                intent,
                knowledge,
                product_catalog,
                regions,
                boundary,
                reviews,
                ai_factor,
            )
        )
    kept = [item for item in decisions if item.match in {"产品/区域/资质相关", "产品相关"}]
    return sorted(kept, key=lambda item: (-item.score, item.query))[:50]


def _score_query_decision(
    query: str,
    intent: str,
    knowledge: EnterpriseKnowledge,
    product_catalog: list[str],
    regions: list[str],
    boundary: list[QualificationBoundary],
    reviews: list[EvidenceReview],
    ai_factor: float,
) -> RecommendationDecision:
    q_lower = query.lower()
    product_hits: list[str] = []
    for product, synonyms in PRODUCT_CATALOG.items():
        if any(synonym.lower() in q_lower for synonym in (product,) + synonyms):
            product_hits.append(product)
    for product in knowledge.products:
        if product and product.lower() in q_lower and product not in product_hits:
            product_hits.append(product)
    product_hits = _dedupe(product_hits)

    requirement_terms = _requirement_terms(query, product_hits)
    # Boundary entries are the source of truth; unknown means not established.
    qualification_status = (
        _qualification_status_for_boundary(knowledge, boundary, requirement_terms)
    )
    product_match = 100 if product_hits else 0
    system_capability = any(word in query for word in SYSTEM_CAPABILITY_WORDS) and _has_system_capability(knowledge)
    capability_match = 100 if system_capability else 75
    if system_capability and product_hits:
        product_match = 100
    regional = next((region for region in regions if region in query), "")
    if not regional:
        regional_match = 100
    else:
        text = " ".join(knowledge.locations + [knowledge.company_text])
        regional_match = 100 if any(term in text for term in REGION_ALIASES.get(regional, (regional,))) else 60
    evidence_terms = product_hits or ([regional] if regional else [])
    requires_evidence = _evidence_gated_query(query)
    evidence_score = (
        _evidence_score_for(knowledge, evidence_terms)
        if requires_evidence and evidence_terms
        else 100
    )
    qualification_match = clamp(100 * QUALIFICATION_MATCH.get(qualification_status, 0.4))

    strong_product = bool(product_hits) and any(hit in product_catalog for hit in product_hits)
    if not strong_product:
        product_match = 0
    score = _fit_score(
        product_match / 100.0,
        capability_match / 100.0,
        qualification_match / 100.0,
        1.0,
        regional_match / 100.0,
        evidence_score / 100.0,
        ai_factor,
    )
    band = recommendation_band(score)
    reason_parts: list[str] = []
    if product_hits:
        reason_parts.append(f"产品/类别匹配：{'、'.join(product_hits[:3])}")
    else:
        reason_parts.append("企业产品目录不覆盖该需求")
    if regional:
        reason_parts.append(f"区域={regional}匹配")
    if requirement_terms:
        reason_parts.append("存在资质型采购要求")
        if qualification_status != "verified":
            reason_parts.append("资质尚未核验/未具备")
    return RecommendationDecision(
        query=query,
        intent=intent,
        match="产品/区域/资质相关" if product_hits or regional else "产品相关",
        recommendation=band,
        score=score,
        reason="；".join(reason_parts) or "按通用条件评估",
        evidence=[item.id for item in reviews[:5]],
        product_match=product_match,
        capability_match=capability_match,
        qualification_match=qualification_match,
        regional_match=regional_match,
        evidence_strength=evidence_score,
    )


def _evidence_gated_query(query: str) -> bool:
    """Only case/acceptance/reputation queries gate the fit on evidence strength."""
    return any(
        word in query
        for word in ("有项目案例", "项目案例", "案例", "验收资料", "独立出具", "可验证", "官方", "招投标")
    )


def _requirement_terms(query: str, product_hits: list[str]) -> list[str]:
    terms: list[str] = []
    q = query.lower()
    for product, qualification in REGULATED_PRODUCT_TERMS.items():
        if product.lower() in q or product in product_hits:
            terms.append(qualification)
    if any(word in q for word in ("完整验收资料", "独立出具", "验收资料")):
        terms.append("完整验收资料")
    return _dedupe(terms)


def _has_system_capability(knowledge: EnterpriseKnowledge) -> bool:
    text = " ".join(knowledge.services + [knowledge.company_text])
    return any(word in text for word in SYSTEM_CAPABILITY_WORDS)


def _competitor_pools(diagnostic: dict[str, Any], knowledge: EnterpriseKnowledge) -> list[CompetitorPool]:
    names = [
        str(item.get("name") or item if isinstance(item, dict) else item).strip()
        for item in diagnostic.get("competitors") or []
    ]
    names = [item for item in names if item]
    if not names:
        return []
    pools = [
        ("持证成品厂家", "direct_competitor"),
        ("系统集成厂家", "indirect_competitor"),
        ("专业设备厂家", "direct_competitor"),
        ("OEM/构件加工厂", "indirect_competitor"),
        ("区域服务商", "scenario_competitor"),
    ]
    result: list[CompetitorPool] = []
    product_catalog = " ".join(knowledge.products + [knowledge.business])
    for index, (pool, relationship) in enumerate(pools, start=1):
        if any(term in pool for term in ("成品", "设备")):
            members = names
        elif any(term in pool for term in ("集成", "区域", "服务")):
            members = names
        else:
            members = names
        if not members:
            continue
        advantage: list[str] = []
        disadvantage: list[str] = []
        if "系统" in pool:
            advantage.append("企业若具备系统集成服务，可竞争整体配套")
            disadvantage.append("竞品若同时持有成品与系统能力，会先吃掉整体项目")
        if "区域" in pool:
            advantage.append("区域服务响应是差异化点")
            disadvantage.append("跨区项目可能输给本地服务商")
        result.append(
            CompetitorPool(
                pool=f"COMPETITOR_POOL_{index} {pool}",
                relationship=relationship,
                members=members[:8],
                basis="竞品池按用户确认/真实观察得到的竞品名单归类；未确认竞品不自动生成。",
                client_advantage=advantage or [f"企业可主张与{pool}相关的自有能力（需证据）"],
                client_disadvantage=disadvantage or [f"竞品在{pool}维度的证据与AI认知可能领先"],
            )
        )
    return result


def _positioning(
    knowledge: EnterpriseKnowledge,
    product_catalog: list[str],
    regions: list[str],
    scenarios: list[CustomerScenario],
    boundary: list[QualificationBoundary],
    decisions: list[RecommendationDecision],
) -> Positioning:
    primary_products = knowledge.products or product_catalog[:2]
    primary = "、".join(primary_products[:2]) + ("生产商" if primary_products else knowledge.business or "企业")
    secondary: list[str] = []
    for capability in _build_capabilities(knowledge).values():
        if capability.type in {"SYSTEM_INTEGRATION", "SERVICE", "PROJECT", "OEM", "CUSTOMIZATION", "DELIVERY"}:
            secondary.append(capability.capability)
    secondary = _dedupe(secondary)[:5]
    recommended_scenarios = [
        item.scenario for item in scenarios if item.recommendation_score >= 75
    ][:6]
    restricted_scenarios = [
        item.scenario for item in scenarios if item.recommendation_score < 60
    ][:4]
    restricted_scenarios += [
        item.item for item in boundary if item.status != "verified"
    ][:3]
    restricted_scenarios = _dedupe(restricted_scenarios)
    tags = primary_products + secondary[:2]
    region_tags = regions or knowledge.locations[:3]
    sentence = f"{knowledge.company_name}定位为{primary}；" if primary else ""
    if regions:
        sentence += f"在{'、'.join(region_tags)}区域项目配套中具备可主张价值。"
    return Positioning(
        primary_positioning=primary,
        secondary_positioning=secondary,
        core_tags=tags,
        regional_tags=region_tags,
        product_authority=primary_products[:5],
        service_authority=secondary[:4],
        recommended_customer_types=_dedupe(
            [SEARCH_CUSTOMER_TYPES.get(customer, customer) for customer in knowledge.customers]
        )[:8],
        recommended_scenarios=recommended_scenarios,
        restricted_scenarios=restricted_scenarios,
        competitive_position="应聚焦能建立证据优势的产品/区域/系统能力，不抢无资质的监管市场标签。",
        one_sentence_positioning=sentence.strip(),
    )


def _promotion_strategy(
    knowledge: EnterpriseKnowledge,
    capabilities: dict[str, Capability],
    boundary: list[QualificationBoundary],
    regions: list[str],
) -> PromotionStrategy:
    capabilities_list = sorted(capabilities.values(), key=lambda item: item.level, reverse=True)
    core = [item.capability for item in capabilities_list if item.type in {"PRODUCT", "MANUFACTURING", "SYSTEM_INTEGRATION", "TECHNICAL"}][:6]
    promote = _dedupe(
        core
        + [f"{region}区域项目配套能力" for region in regions]
        + ["真实项目案例与验收证据" if knowledge.cases else "待建立项目案例库"]
        + ["检测报告与第三方证明" if any(item.status == "verified" for item in boundary) else "待补齐第三方证据"]
    )
    avoid = _dedupe(
        [f"宣传具备{item.item}" for item in boundary if item.status != "verified"]
        + ["无法验证的行业第一/领先/唯一表述"]
        + ["用产品关键词暗示未核验资质"]
    )
    priorities = [
        {"priority": "P0", "direction": "核心产品 + 可验证能力", "action": "以产品参数、检测报告、资质原文建立核心证据页"},
        {"priority": "P1", "direction": "项目案例 + 区域经验", "action": "发布可溯源的案例/项目/区域服务内容"},
        {"priority": "P2", "direction": "技术内容 + FAQ", "action": "围绕产品选型、系统集成、验收口径做技术内容"},
        {"priority": "P3", "direction": "品牌故事 + 企业文化", "action": "补充企业沿革、质量体系与客户口碑"},
    ]
    return PromotionStrategy(promote=promote, avoid=avoid, priorities=priorities)


def _claim_safety(
    knowledge: EnterpriseKnowledge,
    boundary: list[QualificationBoundary],
) -> list[ClaimSafety]:
    claims: list[ClaimSafety] = []
    seen: set[str] = set()
    raw = knowledge.company_raw

    def add_claim(claim: str, status: str, reason: str, evidence: list[str] | None = None, recommendation: str = "") -> None:
        claim = claim.strip()
        if not claim or claim in seen:
            return
        seen.add(claim)
        claims.append(
            ClaimSafety(
                claim=claim,
                status=status,
                evidence=list(evidence or []),
                reason=reason,
                recommendation=recommendation or "保持现状；发布前确认有可核验来源。",
            )
        )

    for product in knowledge.products:
        status = "MARKETING_CLAIM" if any(pattern in product for pattern in MARKETING_CLAIM_PATTERNS) else "UNVERIFIED"
        add_claim(
            f"企业生产/供应{product}",
            status,
            "来源为用户提供资料，未完成独立核验。" if status == "UNVERIFIED" else "表述含夸大或不可验证词汇。",
            _evidence_ids_for_claim(knowledge, product),
        )
    for service in knowledge.services:
        add_claim(
            f"企业提供{service}",
            "UNVERIFIED",
            "来源为用户提供资料，未完成独立核验。",
            _evidence_ids_for_claim(knowledge, service),
        )
    for certificate in knowledge.certificates:
        verified = certificate in [item.item for item in boundary if item.status == "verified"]
        add_claim(
            f"企业持有{certificate}",
            "FACT" if verified else "UNVERIFIED",
            "已绑定官方/可核验来源。" if verified else "用户提供证书或描述，未独立核验。",
            [],
        )
    for evidence in knowledge.evidence:
        claim = str(evidence.get("claim") or "").strip()
        if not claim:
            continue
        if any(pattern in claim for pattern in MARKETING_CLAIM_PATTERNS):
            status = "MARKETING_CLAIM"
        elif evidence.get("verified"):
            status = "FACT"
        elif evidence.get("conflicts_with"):
            status = "CONFLICT"
        else:
            status = "UNVERIFIED"
        add_claim(
            claim,
            status,
            "官方/已核验来源支持。" if status == "FACT" else "存在冲突来源，需裁决。" if status == "CONFLICT" else "存在夸大/绝对化表述，不能升级为事实。" if status == "MARKETING_CLAIM" else "来源未核验。",
            [str(evidence.get("id") or "")],
        )
    return claims


def _evidence_ids_for_claim(knowledge: EnterpriseKnowledge, term: str) -> list[str]:
    return [
        str(item.get("id") or "")
        for item in knowledge.evidence
        if term and term.lower() in str(item.get("claim") or "").lower()
    ]


def _geo_content_gaps(
    knowledge: EnterpriseKnowledge,
    capabilities: dict[str, Capability],
    boundary: list[QualificationBoundary],
    regions: list[str],
    scenarios: list[CustomerScenario],
) -> list[GeoContentGap]:
    gaps: list[GeoContentGap] = []
    third_party = [item for item in knowledge.evidence if str(item.get("source_type") or "") in {"government", "media", "third_party"}]
    if not third_party:
        gaps.append(
            GeoContentGap(
                gap_type="Missing Third-party Proof",
                severity="high",
                reason="全部证据来自用户提供/企业官方，缺少第三方或监管来源。",
                suggestion="优先补官方资质查询结果、招投标平台、行业媒体或独立报道。",
            )
        )
    unverified = [item for item in boundary if item.status != "verified"]
    if unverified:
        gaps.append(
            GeoContentGap(
                gap_type="Missing Evidence",
                severity="high",
                reason=f"{len(unverified)} 项资质/边界尚未核验：{'、'.join(item.item for item in unverified[:3])}。",
                suggestion="逐项提供官方来源并建立核验档案，避免资质相关营销表述。",
            )
        )
    if not knowledge.products:
        gaps.append(
            GeoContentGap(
                gap_type="Missing Content",
                severity="high",
                reason="未识别到结构化的核心产品内容。",
                suggestion="补充产品目录、参数、检测报告与使用场景内容。",
            )
        )
    if not knowledge.cases:
        gaps.append(
            GeoContentGap(
                gap_type="Missing Content",
                severity="medium",
                reason="缺少真实项目案例，区域/项目证据弱。",
                suggestion="建立项目案例数据库，记录可公开的项目名称、区域、内容和验收状态。",
            )
        )
    if regions and not any(item.regional_match >= 90 for item in scenarios):
        gaps.append(
            GeoContentGap(
                gap_type="Missing Scenario",
                severity="medium",
                reason=f"区域={'、'.join(regions)}匹配度高但项目/案例证据不足，AI 缺少推荐理由。",
                suggestion="发布区域项目证据与区域服务 FAQ。",
            )
        )
    if not knowledge.ai_observations:
        gaps.append(
            GeoContentGap(
                gap_type="Missing Query",
                severity="medium",
                reason="没有真实 AI 观察，无法判断当前推荐/缺失查询。",
                suggestion="使用本报告的 Recommended/Restricted Query 清单建立真实 AI 测试基线。",
            )
        )
    return gaps


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    result: list[str] = []
    for item in value if isinstance(value, (list, tuple)) else [value]:
        if isinstance(item, dict):
            item = str(item.get("name") or item.get("value") or item.get("title") or "")
        text = str(item or "").strip()
        if text and text not in result and not is_unknown(text):
            result.append(text)
    return result


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return result
