---
name: geo-bd-diagnostic-skill
description: 企业 GEO 优化前诊断与背调：把官网、文档、PDF、产品资料和案例整理为企业实体、AI 认知、Query 覆盖、Evidence、竞品差距、GEO Score 与 P0-P3 优化路线。用于明确后续 GEO Strategy；不负责内容生产和 GEO Production 执行。
---

# GEO-BD Diagnostic Skill V1.0

这个 Skill 是 GEO 生态的诊断入口。它只负责回答“企业当前是什么状态、AI 怎么理解、为什么不被推荐、下一步先优化什么”，结果交给后续 GEO Strategy 和 GEO Production 使用。

## 工作流

```text
Client Materials
  -> Material Intelligence
  -> Enterprise Profile
  -> AI Visibility
  -> Query Intelligence
  -> Evidence / E-E-A-T / E-E-A-P
  -> Competitor Gap
  -> GEO Score
  -> Insight Engine
  -> GEO Diagnostic Report
```

先把客户材料整理为 `geo-account-precheck/inputs/diagnostic-template.json` 兼容的 JSON，再运行：

```bash
cd geo-account-precheck
python3 scripts/run_geo_bd_diagnostic.py \
  --input tests/cases/dezhou-tuosheng/company.json \
  --output /tmp/geo-bd-diagnostic.md \
  --json /tmp/geo-bd-diagnostic.json \
  --offline
```

## 必须输出的九个部分

1. 企业当前状态
2. AI 认知分析
3. Query 覆盖分析：Brand、Business、Scenario、Commercial
4. Evidence 可信度：Experience、Expertise、Evidence、Authority、Proof
5. 竞品差距
6. GEO Score：Entity、AI Visibility、Query Coverage、Evidence、Authority 各 20 分
7. GEO 缺口
8. P0-P3 优化建议
9. 下一阶段执行路线

五类分数必须来自现有诊断结果。缺失数据使用 `UNKNOWN`、`NOT_RUN` 或
`INSUFFICIENT_DATA`；缺失类别不按 0 计入总分，五类数据齐全后才输出 100 分制总分。

## 资料和事实边界

- 客户材料可作为 `FACT`，来源标记为 `user_provided`，不能冒充外部核验事实。
- 真实 AI 回答才可用于 AI 认知、推荐、引用和 Query 覆盖；`simulated` 永不计分。
- 竞品必须有来源和 `candidate/confirmed` 状态，不能自动发明竞品。
- Evidence 必须保留声明、来源、日期、核验状态和冲突信息。
- 诊断分数是当前状态指标，不是任何 AI 平台的排名保证。

## 代码路由

- 主流程：`geo-account-precheck/engine/pipeline.py`
- V1 输出适配：`geo-account-precheck/engine/reporting/diagnostic_skill.py`
- V1 命令：`geo-account-precheck/scripts/run_geo_bd_diagnostic.py`
- V1 Schema：`skills/geo-bd-diagnostic-skill/references/diagnostic-output.schema.json`
- V1 报告模板：`skills/geo-bd-diagnostic-skill/references/report-template.md`
- Golden Case：`geo-account-precheck/tests/cases/case_001_tuoshi_ventilation/`

详细输出契约见 `references/diagnostic-contract.md`；只在需要检查字段或扩展输出时读取。
