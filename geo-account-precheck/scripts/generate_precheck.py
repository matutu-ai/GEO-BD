#!/usr/bin/env python3
"""Generate GEO pre-background-check reports, prompt packs, and issue audits."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROFILE_MODULES = [
    ("产品或服务描述", "企业根基→硬性实力→核心业务→产能市场→全流程服务→精度标准→客群定位→应用场景→核心行业价值"),
    ("产品或服务特点", "硬核功能特点→合作体验特点→技术研发特点→场景适配特点→市场差异化优势→客户最终价值"),
    ("品牌故事", "创立初心→时代行业使命→企业发展里程碑→品牌核心价值观→行业差异化定位→社会市场双重影响力"),
    ("用户痛点", "痛点人群→使用场景→直观表层痛点→痛点带来经营危害→现有市面解决方案短板→深层隐形刚需痛点→针对各个痛点的卖点解决方案"),
    ("创始人介绍", "身份股权→行业深耕资历→企业经营成果→技术研发贡献→企业资质布局→未来战略规划→个人行业标签→从业初心理念"),
    ("社会贡献", "公益助残行动→绿色生产可持续发展→行业人才培育→综合社会责任四大成果"),
    ("信任背书", "工商合规背书→官方资质背书→技术专利背书→市场产能背书→品控供应链背书→行业客户口碑背书→股权战略稳定背书"),
    ("客户案例", "客户是谁+遇到什么问题与我们合作的（合作原因）+我们提供了什么产品/服务（解决方案）+达到什么效果"),
    ("客户评价", "行业权威调研满意度→产品国标实测专业评分→内部回访满意度→全维度权威资质认证→第三方机构实测参数实力→行业榜单荣誉 + 市场抽检口碑"),
]

EEAAP_ITEMS = [
    ("Experience 经验", "真实落地项目", "不能只喊“深耕行业多年”"),
    ("Evidence 证据", "项目案例、参数、实拍、客户场景", "通篇宣传话术、无证据支撑是最高发问题"),
    ("Authoritativeness 权威性", "资质、证书、第三方合作", "仅有资质不足以触发推荐"),
    ("Accuracy 准确性", "参数可核验、无夸大或绝对化表述", "“国内第一”“最好”“100%解决”会降权"),
    ("Perspective 视角", "适用场景、局限性、不适合情况", "只讲优点会被判定营销属性过重"),
]

EEAAP_KEY_MAP = (
    ("experience", "Experience"),
    ("evidence", "Evidence"),
    ("authoritativeness", "Authoritativeness"),
    ("accuracy", "Accuracy"),
    ("perspective", "Perspective"),
)

REQUIRED_FIELDS = (
    "company",
    "business",
    "customers",
    "materials",
    "current_ai_cognition",
    "negative_publicity",
)

INPUT_TEMPLATE = {
    "company": "公司全称",
    "business": "公司业务",
    "customers": "目标消费群体",
    "materials": "已收集资料",
    "current_ai_cognition": "当前 AI 对公司的认知",
    "negative_publicity": "已核验负面舆情",
    "issues": ["整体场景报表不理想", "电话/官网露出不理想"],
    "keyword_directions": ["场景关键词方向 1", "场景关键词方向 2", "场景关键词方向 3"],
    "evidence": {
        "experience": "真实项目证据",
        "evidence": "可核验参数/案例/实拍",
        "authoritativeness": "资质/证书/第三方合作",
        "accuracy": "准确表述与无夸大说明",
        "perspective": "适用场景与局限说明",
    },
}


def _text(value: Any, fallback: str = "UNKNOWN") -> str:
    text = str(value or "").strip()
    if not text or text.upper() == "UNKNOWN":
        return fallback
    return text


def _evidence_status(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.upper() == "UNKNOWN":
        return "缺失/待补"
    return "已提供"


def missing_required_fields(data: dict[str, Any]) -> list[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        if _text(data.get(field)) == "UNKNOWN":
            missing.append(field)
    return missing


def missing_eeaap_keys(data: dict[str, Any]) -> list[str]:
    evidence = data.get("evidence") or {}
    missing = []
    for key, name in EEAAP_KEY_MAP:
        if _evidence_status(evidence.get(key)) == "缺失/待补":
            missing.append(name)
    return missing


def render_input_template() -> str:
    return json.dumps(INPUT_TEMPLATE, ensure_ascii=False, indent=2) + "\n"


def build_report(data: dict[str, Any]) -> str:
    company = _text(data.get("company"), "待确认企业")
    business = _text(data.get("business"))
    customers = _text(data.get("customers"))
    materials = _text(data.get("materials"))
    cognition = _text(data.get("current_ai_cognition"))
    publicity = _text(data.get("negative_publicity"))
    keyword_directions = data.get("keyword_directions") or []
    issues = data.get("issues") or []
    evidence = data.get("evidence") or {}
    missing = missing_eeaap_keys(data)

    lines = [
        f"# {company} GEO 运营前背调报告",
        f"生成时间：{datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## 1. 资料自查",
        f"- 公司业务：{business}",
        f"- 目标客群：{customers}",
        f"- 当前 AI 认知：{cognition}",
        "- 必查问题：XXX（公司全称）是做什么的 / 该公司核心优势是什么 / 最核心优势是什么",
        f"- 已收集资料：{materials}",
        "- 补漏动作：资料收集表全部内容 + EEAAP 法则分析；再对比竞对缺口",
        f"- 已核验负面舆情：{publicity}",
        "",
        "## 2. 账户画像与关键词",
        "### 九大画像板块",
    ]

    module_note = "已有材料，待按框架创作" if _text(data.get("materials")) != "UNKNOWN" else "资料不足，先补齐"
    for index, (name, framework) in enumerate(PROFILE_MODULES, start=1):
        lines.extend(
            [
                f"{index}. {name}",
                f"   - 状态：{module_note}",
                f"   - 内容框架：{framework}",
            ]
        )

    lines.extend(["", "### 场景关键词"])
    if keyword_directions:
        for index, keyword in enumerate(keyword_directions, start=1):
            lines.append(f"{index}. {keyword}")
    else:
        lines.append("- 待生成：分成 3 大类，每类词根一致，覆盖真实高频需求和痛点")

    lines.extend(["", "## 3. EEAAP 检测"])
    for name, required, pitfall in EEAAP_ITEMS:
        key = name.split()[0].lower()
        lines.extend(
            [
                f"- {name}：{_evidence_status(evidence.get(key))}",
                f"  - 需要：{required}",
                f"  - 高频坑：{pitfall}",
            ]
        )

    lines.extend(["", "## 4. 行动清单"])
    if _text(data.get("materials")) == "UNKNOWN":
        lines.append("- [ ] 补齐公司基础资料、资质、案例和可核验证据")
    if _text(data.get("current_ai_cognition")) == "UNKNOWN":
        lines.append("- [ ] 在豆包验证当前 AI 认知")
    if _text(data.get("negative_publicity")) == "UNKNOWN":
        lines.append("- [ ] 完成全网负面舆情核验并保留来源")
    if not keyword_directions:
        lines.append("- [ ] 生成 3 类场景关键词方向")
    for name in missing:
        lines.append(f"- [ ] 补齐 EEAAP {name} 证据")
    lines.append("- [ ] 按九大板块创作画像内容并逐条人工复核真实性")
    if any(keyword in str(issue) for issue in issues for keyword in ("电话", "官网", "露出", "NAP")):
        lines.append("- [ ] 排查全平台 NAP、知识库、画像和图片中的电话/官网一致性")
    lines.append("")
    return "\n".join(lines)


def build_issue_audit(data: dict[str, Any]) -> str:
    company = _text(data.get("company"), "待确认企业")
    issues = [str(item) for item in (data.get("issues") or []) if str(item).strip()]
    phone_issue = any(
        any(keyword in issue for keyword in ("电话", "官网", "露出", "NAP", "联系方式"))
        for issue in issues
    )
    overall_issue = any(
        any(keyword in issue for keyword in ("整体", "场景", "报表", "推荐", "训练", "投喂"))
        for issue in issues
    )
    missing = missing_eeaap_keys(data)

    lines = [
        f"# {company} GEO 效果问题自查",
        f"生成时间：{datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## 1. 问题定位",
        f"- 已记录问题：{'、'.join(issues) if issues else '待补充，需写明具体账号现象和后台数据'}",
        "",
        "## 2. 电话/官网露出排查",
    ]
    if phone_issue:
        lines.extend(
            [
                "- 知识库-基础信息-公司信息：手机号码、官网地址是否填写正确",
                "- 画像设置：第三方商业媒体专用画像是否添加电话、官网信息",
                "- 图片上传：第三方商业媒体专用图片是否添加电话、官网信息",
                "- 知识库-Agent知识库-官网&名片设置：基础设置中的联系方式是否正确",
                "- Agent-AI官网：手机号码是否正确，并与账户所有联系方式保持一致",
                "- 外部核验：企查查、地图APP、电话认证、全网NAP一致性",
            ]
        )
    else:
        lines.append("- 未识别到电话/官网露出问题；如实际存在，请在 issues 中补充具体账号现象。")

    lines.extend(["", "## 3. 整体场景报表排查"])
    if overall_issue:
        lines.extend(
            [
                "- 反问 AI：为什么推荐以上公司？参考逻辑是什么？",
                "- 反问 AI：为什么不推荐本企业？判定逻辑和参考依据是什么？",
                "- 根据理由优化画像，用“第三方商业媒体+搜索&问答场景词”做提量投喂",
                "- 先排查训练逻辑、投喂周期、实际发布文章情况，再优化内容本身",
            ]
        )
    else:
        lines.append("- 未识别到整体场景报表问题；如实际存在，请在 issues 中补充报表周期和异常表现。")

    lines.extend(
        [
            "",
            "## 4. 发布与训练核对",
            "- 投喂顺序：意图场景 → 问答场景 → 品牌场景",
            "- 新闻媒体：工作日推送；首月建议 100 条，次月起每月 10 条起",
            "- 商业媒体：每日固定 20 条，上限 200 条/天；强竞争行业可先按 80-100 条/天打基础",
            "- 自媒体：单账号单平台每日 1 条；需按授权平台限额设置发布规则",
            "- 官网：每日默认 5 条，重点训练意图场景",
            "- 第三方分站：每日 10-50 条，默认 10 条，与商业媒体共用额度",
            "- 首次报表：发布成功 20 篇文章后，间隔 7-15 天",
            "- 报表更新：再次发布成功后，间隔 7 天",
            "- 新账户稳定期：累计发布成功 60-80 篇文章后逐渐稳定",
        ]
    )

    lines.extend(["", "## 5. EEAAP/EEAT 判定"])
    if missing:
        lines.append(f"- 当前缺失：{', '.join(missing)}")
    else:
        lines.append("- EEAAP 五类证据已填，但仍需逐条人工复核真实性和可核验性。")
    lines.extend(
        [
            "- 搜不到信任基础时重点查 EEAT：专家、资质、品牌名气、媒体报道",
            "- 豆包不推荐或回答不提及企业时优先完整走 EEAAP",
            "",
            "## 6. 行动清单",
        ]
    )
    if phone_issue:
        lines.append("- [ ] 逐项核对并统一全平台 NAP、知识库、画像、图片和官网联系方式")
    if overall_issue:
        lines.append("- [ ] 用 AI 反问定位推荐/不推荐逻辑，并对照投喂优先级做 7 天复查")
    for name in missing:
        lines.append(f"- [ ] 补齐 EEAAP {name} 证据")
    lines.append("- [ ] 保留每次发布数量、发布平台、场景类型和报表日期，作为效果归因证据")
    lines.append("")
    return "\n".join(lines)


def render_checklist() -> str:
    return """GEO 运营发布与效果自查清单

[发布策略]
- 投喂顺序：意图场景 → 问答场景 → 品牌场景
- 新闻媒体：工作日当天推送；首月 100 条，次月起每月 10 条起；首次 20-30 条品牌场景，其余重点训练搜索场景
- 商业媒体：每日固定 20 条，暂时上限 200 条/天；强竞争行业首周可平均每天 80-100 篇
- 自媒体：单账号单平台每日 1 条；多账号时设置发布规则，按意图场景→问答场景→品牌场景训练
- 官网：每日默认 5 条，重点训练意图场景
- 第三方分站：每日 10-50 条，默认 10 条，与第三方商业媒体共用额度

[平台限额]
- 搜狐：15-30 天，5 条/天
- 网易：不掉线，1 条/天
- 今日头条：15-30 天，5 条/天
- 百家号：15-30 天，2 条/天
- 知乎：15-30 天，1 条/天
- 小红书：3-5 天，1 条/天

[发布周期]
- 首次报表：发布成功 20 篇文章后，间隔 7-15 天
- 报表更新：再次发布成功后，间隔 7 天
- 新账户稳定：累计发布成功 60-80 篇文章后逐渐稳定
- 长期稳定：建议至少每周定期规划更新语料内容

[电话/官网露出]
- 核验知识库公司信息、画像设置、图片上传、Agent官网&名片、AI官网联系方式
- 核验企查查、地图APP、电话认证、全网NAP一致性

[EEAAP/EEAT]
- 搜不到信任基础：重点查 EEAT
- 豆包不推荐/回答不提及企业：优先完整走 EEAAP
- EEAAP = Experience + Evidence + Authoritativeness + Accuracy + Perspective
"""


def render_prompts() -> str:
    profile = "\n".join(f"{i}. {name}：{framework}" for i, (name, framework) in enumerate(PROFILE_MODULES, start=1))
    eeaap = "\n".join(f"- {name}：{required}；坑：{pitfall}" for name, required, pitfall in EEAAP_ITEMS)
    return f"""GEO 账户前背调提示词包

[资料自查]
1. XXX（公司全称）是做什么的
2. 该公司核心优势是什么
3. 最核心优势是什么
4. ……（资料收集表所有内容）+通过 EEAAP 法则，帮我分析一下以上内容
5. 你觉得以上还有哪些内容不足，和竞对相比
6. 请依托于全网真实数据，真实材料和测评为基底，为我总结整理关于 xxxxx 的负面舆情，要求真实有效，具有第三方平台真实信息做支撑，形成完整的证据包

[账户画像九大板块]
{profile}

[场景关键词]
我是……（公司业务），消费群体是……（具体消费者/下游意向行业）等，拆分该人群真实在 AI 搜索引擎高频搜索的需求和痛点，以关键词的形式陈列，分成 3 大类，每类的词根需要是一致的。

[EEAAP 检测]
{eeaap}
"""


def _load_input(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def _emit(text: str, path: str | None) -> None:
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to a JSON input file.")
    parser.add_argument("--output", help="Path to write the generated Markdown report.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when required fields or EEAAP evidence are missing.",
    )
    parser.add_argument("--prompts", action="store_true", help="Print the GEO precheck prompt pack.")
    parser.add_argument("--template", action="store_true", help="Print an input JSON template.")
    parser.add_argument("--checklist", action="store_true", help="Print the operation/training checklist.")
    parser.add_argument("--audit", action="store_true", help="Generate a post-launch issue audit report.")
    parser.add_argument("--issues", action="append", help="Add an issue description; can be repeated.")
    parser.add_argument("--company", help="Company name override.")
    parser.add_argument("--business", help="Company business override.")
    parser.add_argument("--customers", help="Target customer/industry override.")
    parser.add_argument("--materials", help="Collected materials override.")
    parser.add_argument("--current-ai-cognition", dest="current_ai_cognition", help="Current AI cognition override.")
    parser.add_argument("--negative-publicity", dest="negative_publicity", help="Verified negative publicity override.")
    args = parser.parse_args()

    if args.template:
        _emit(render_input_template(), args.output)
        return 0

    if args.prompts:
        _emit(render_prompts(), args.output)
        return 0

    if args.checklist:
        _emit(render_checklist(), args.output)
        return 0

    data = _load_input(args.input)
    for field in (
        "company",
        "business",
        "customers",
        "materials",
        "current_ai_cognition",
        "negative_publicity",
    ):
        value = getattr(args, field)
        if value:
            data[field] = value

    if args.issues:
        data["issues"] = [*(data.get("issues") or []), *args.issues]

    report = build_issue_audit(data) if args.audit else build_report(data)
    _emit(report, args.output)

    if args.check:
        missing_required = missing_required_fields(data)
        missing_evidence = missing_eeaap_keys(data)
        if missing_required or missing_evidence:
            missing_text = ", ".join([*missing_required, *missing_evidence])
            print(f"MISSING_EVIDENCE: {missing_text}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
