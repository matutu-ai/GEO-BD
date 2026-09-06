"""Query intent classification."""

from __future__ import annotations

from typing import Iterable

INTENT_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("comparison", ("对比", "哪个好", " vs ", "versus", "区别")),
    ("recommendation", ("推荐", "值得", "靠谱", "哪家", "哪些厂家", "哪些品牌")),
    ("decision", ("应该选", "如何选择", "怎么选", "选择", "购买建议", "下单", "靠谱吗")),
    ("local", ("附近", "本地", "周边", "哪里", "同城", "城市")),
    ("problem", ("坏了", "故障", "不制冷", "不冷", "漏水", "维修", "出问题", "痛点")),
    ("commercial", ("价格", "报价", "多少钱", "费用", "成本", "厂家", "供应商")),
    ("informational", ("是什么", "做什么", "怎么样", "主营", "优势", "如何", "怎么", "为什么")),
    ("product", ("产品", "设备", "品牌", "型号", "参数")),
]

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
}


def classify_query(query: str, company_mentioned: bool = False, fallback: str = "unknown") -> str:
    text = query.lower().strip()
    if not text:
        return fallback
    for intent, keywords in INTENT_RULES:
        if any(keyword in text for keyword in keywords):
            return intent
    if company_mentioned:
        return "brand"
    if any(keyword in text for keyword in ("厂家", "公司", "供应商", "服务商", "机构")):
        return "commercial"
    return fallback


def intent_label(intent: str) -> str:
    return INTENT_LABELS.get(intent, intent)


def covered_intents(queries: Iterable[object]) -> set[str]:
    intents = set()
    for query in queries:
        intent = getattr(query, "intent", None) or str(query).lower()
        if intent and intent != "unknown":
            intents.add(intent)
    return intents
