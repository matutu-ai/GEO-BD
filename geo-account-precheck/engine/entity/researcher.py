"""Entity researcher: converts client materials into a structured entity."""

from __future__ import annotations

from typing import Any

from ..common import ALLOWED_RESEARCH_MODES, FACT, is_unknown, listify
from ..models.company import CompanyProfile
from ..models.entity import EntityProfile, FactValue


CATEGORY_ORDER = [
    "name",
    "aliases",
    "brands",
    "business",
    "industry",
    "products",
    "services",
    "customers",
    "cases",
    "locations",
    "founders",
    "experts",
    "certificates",
    "patents",
    "media",
    "website",
    "contacts",
    "address",
    "phone",
    "social_accounts",
    "reviews",
    "third_party_profiles",
    "competitors",
    "negative_information",
]

REQUIRED_KEYS = {
    "name": ("企业名称", 0.18),
    "business": ("主营业务", 0.14),
    "products": ("产品", 0.08),
    "services": ("服务", 0.08),
    "customers": ("目标客群", 0.08),
    "cases": ("客户案例", 0.05),
    "locations": ("地域", 0.08),
    "industry": ("行业", 0.08),
    "website": ("官网", 0.05),
    "contacts": ("联系方式", 0.05),
    "address": ("地址", 0.04),
    "phone": ("电话", 0.03),
    "social_accounts": ("社交媒体", 0.03),
    "reviews": ("客户评价", 0.02),
    "founders": ("创始人", 0.04),
    "experts": ("专家", 0.03),
    "certificates": ("资质", 0.03),
    "media": ("媒体报道", 0.03),
    "negative_information": ("负面信息", 0.05),
}

FIELD_LABELS = {
    "name": "企业名称",
    "aliases": "企业别名",
    "brands": "品牌名",
    "business": "主营业务",
    "industry": "行业",
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
    "third_party_profiles": "第三方平台",
    "competitors": "竞品",
    "negative_information": "负面信息",
}


class EntityResearcher:
    """Builds an EntityProfile from operator-provided data.

    mode='offline' guarantees no external calls.  Anything not supplied stays
    UNKNOWN with confidence 0.
    """

    def __init__(self, mode: str = "offline") -> None:
        if mode not in ALLOWED_RESEARCH_MODES:
            mode = "offline"
        self.mode = mode

    def research(self, company_profile: CompanyProfile) -> EntityProfile:
        profile = EntityProfile(research_mode=self.mode, raw_materials=company_profile.materials)
        company_raw = company_profile.raw.get("company") or {}
        if not isinstance(company_raw, dict):
            company_raw = {}

        for key in CATEGORY_ORDER:
            values = _collect_values(company_profile, company_raw, key)
            if values:
                profile.fields[key] = [
                    FactValue(
                        value=value,
                        status=FACT,
                        confidence=60,
                        source="用户提供资料",
                        source_type="user_provided",
                        verified=False,
                    )
                    for value in values
                ]
            else:
                profile.fields[key] = [FactValue.unknown()]
                if key in REQUIRED_KEYS:
                    profile.missing.append(key)
        return profile


def _collect_values(company_profile: CompanyProfile, company_raw: dict[str, Any], key: str) -> list[str]:
    if key == "name" and company_profile.name:
        return [company_profile.name]
    if key == "business" and company_profile.business:
        return [company_profile.business]

    source_values = company_raw.get(key)
    if key == "aliases" and company_profile.aliases:
        source_values = company_profile.aliases
    if key == "industry" and company_profile.industry:
        source_values = company_profile.industry
    if key == "customers" and company_profile.customers:
        source_values = company_profile.customers
    if key == "locations" and company_profile.locations:
        source_values = company_profile.locations
    if source_values is None:
        return []

    values = listify(source_values)
    return [value for value in values if value and not is_unknown(value)]
