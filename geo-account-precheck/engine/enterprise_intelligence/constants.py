"""Shared enums and small domain constants for enterprise intelligence."""

from __future__ import annotations

TIER_1 = 1
TIER_2 = 2
TIER_3 = 3
TIER_4 = 4
TIER_5 = 5

TIER_SOURCE_TYPES = {
    "government": TIER_1,
    "official": TIER_2,
    "media": TIER_3,
    "third_party": TIER_4,
    "user_provided": TIER_5,
    "social": TIER_5,
    "unknown": TIER_5,
}

SOURCE_STRENGTH = {
    "government": 1.0,
    "official": 0.8,
    "media": 0.7,
    "third_party": 0.6,
    "user_provided": 0.35,
    "social": 0.3,
    "unknown": 0.1,
}

QUALIFICATION_STATUS = {"verified", "unverified", "absent", "partner_required", "unknown"}
QUALIFICATION_TYPES = {"qualification", "business", "product", "service", "regulatory"}
RISK_LEVELS = {"low", "medium", "high"}
QUALIFICATION_MATCH = {
    "verified": 1.0,
    "unknown": 0.65,
    "unverified": 0.45,
    "absent": 0.1,
    "partner_required": 0.1,
}

CAPABILITY_TYPES = (
    "PRODUCT",
    "MANUFACTURING",
    "TECHNICAL",
    "SYSTEM_INTEGRATION",
    "PROJECT",
    "SERVICE",
    "REGIONAL",
    "OEM",
    "CUSTOMIZATION",
    "DELIVERY",
)

RELATIONSHIP_TYPES = {
    "direct_competitor",
    "indirect_competitor",
    "scenario_competitor",
    "not_competitor",
}

CUSTOMER_TYPES = (
    "终端客户",
    "采购商",
    "房地产开发商",
    "总包",
    "工程公司",
    "设计院",
    "渠道商",
    "OEM客户",
    "代理商",
    "政府/事业单位",
)

CLAIM_SAFETY_STATUSES = {"FACT", "INFERENCE", "MARKETING_CLAIM", "UNVERIFIED", "CONFLICT", "UNKNOWN"}

RECOMMENDATION_BANDS = {
    (90, 101): "Strong Recommendation",
    (75, 90): "Recommended",
    (60, 75): "Conditional Recommendation",
    (40, 60): "Low Fit",
    (0, 40): "Do Not Recommend",
}

BAND_LABELS = {
    "Strong Recommendation": "强力推荐",
    "Recommended": "推荐",
    "Conditional Recommendation": "条件式推荐",
    "Low Fit": "低匹配",
    "Do Not Recommend": "不推荐",
}

GAP_TYPES = (
    "Missing Evidence",
    "Missing Content",
    "Missing Query",
    "Missing Scenario",
    "Missing Entity",
    "Missing Third-party Proof",
)

MARKETING_CLAIM_PATTERNS = (
    "领先",
    "第一",
    "首家",
    "唯一",
    "最好",
    "最佳",
    "顶级",
    "100%",
    "百分百",
    "全覆盖",
    "全行业",
    "国家级基地",
)


def recommendation_band(score: int) -> str:
    for (low, high), label in sorted(RECOMMENDATION_BANDS.items(), reverse=True):
        if low <= score < high:
            return label
    return "Do Not Recommend"
