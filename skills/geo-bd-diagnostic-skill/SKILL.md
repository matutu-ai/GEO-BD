---
name: geo-bd-diagnostic-skill
description: 根据客户名称或基础资料快速生成一页 GEO 诊断，输出客户定位、当前 AI/GEO 状态、最多五个主要问题和 P0/P1/P2 优化方向。当用户需要快速看懂客户现状和下一步方向时使用；不生成关键词、画像、内容、发布计划或媒体投放计划。
---

# GEO-BD Diagnostic Skill

## Purpose

GEO-BD 是轻量企业 GEO 快速诊断入口，不是背调平台或内容生产工具。它内部负责：

```text
事实 → 判断 → 根因 → 处方
```

对外只回答“客户是谁、AI 怎么看、主要问题、下一步方向”。处方描述应修复的能力、
依据和验收方法；后续关键词、画像、内容、发布、运营和复测执行全部交给 GEO。

## Standard Workflow

```text
客户输入 / 公开事实
→ Facts
→ Evidence Verification
→ Diagnostic Measurements
→ Judgments
→ Root Causes
→ Prescriptions
→ Report Projection
```

执行规则：

1. 只采集客户明确提供、公开来源记录或真实观察到的资料。
2. 每条 Fact 都保留来源 ID；无法确认的内容使用 `UNKNOWN`。
3. Evidence Verification 记录核验方法、来源、冲突和结论。
4. Diagnostic Measurement 必须引用 Fact 或 Evidence。
5. Judgment 必须引用 Fact ID 或 Diagnostic Metric ID。
6. Root Cause 必须引用 Judgment ID。
7. Prescription 必须引用 Root Cause ID。
8. Report Projection 只能读取和展示上述结果。

缺少依据时停止推导；不得为了报告完整而补写判断或处方。

内部 Facts、Evidence、Measurements、Judgments、Root Causes、Prescriptions 不直接
展示给最终用户。

## One-page Output

最终输出固定为：

```text
# 客户 GEO 快速诊断
## 一、客户定位
## 二、当前 AI / GEO 状态
## 三、当前主要问题（最多 5 条）
## 四、下一步优化方向（P0 / P1 / P2）
## 五、诊断依据（3—5 条）
```

报告控制在一页左右。禁止展示多套 Score、Gap、九大画像、关键词矩阵、内容矩阵、
30/60/90 天计划、技术 Schema、Agent 运行过程或大段 JSON。

## Forbidden Outputs

本 Skill 不得生成：

- 关键词或关键词扩展
- 用户画像、客户画像、内容画像或搜索画像
- 内容、标题、文章、FAQ 或脚本
- 发布计划或固定 30/60/90 天运营计划
- 媒体投放计划
- 目标市场 Query
- GEO 运营和复测执行结果

外部真实测试 Query 可以作为 `PROVIDED` 或 `OBSERVED` Fact 使用，但不能由 GEO-BD
自动生成。

## Diagnostic Contract

唯一标准 Schema 是：

`../../geo-account-precheck/schemas/diagnostic.schema.json`

标准顶层是内部合同；其中只有 `report_projection` 对用户可见：

```text
contract_version
meta
facts
evidence_verification
diagnostic_measurements
judgments
root_causes
prescriptions
report_projection
```

完整结构、ID 规则、状态矩阵和引用要求见
[references/diagnostic-contract.md](references/diagnostic-contract.md)。需要检查字段或扩展输出
时必须先读该文件。

## Status Vocabulary

唯一允许状态：

```text
VERIFIED
OBSERVED
PROVIDED
INFERRED
UNKNOWN
NOT_RUN
INSUFFICIENT_DATA
```

`INFERRED` 禁止进入 Facts。`UNKNOWN`、`NOT_RUN`、`INSUFFICIENT_DATA` 对应的
Diagnostic Measurement 值必须是 `null`，不得自动变成 `0` 或 `100`。

## Report Boundary

报告层只做投影：字段映射、分组、展示裁剪和格式转换。报告层不得重新评分、生成
Gap、形成新 Judgment、定位新 Root Cause、生成新 Prescription 或修改优先级。

## Legacy Transition

阶段 0 仅冻结合同，当前 Python Pipeline 和 V1/V2/V3 兼容输出仍然保留。旧输出使用
`../../geo-account-precheck/schemas/diagnostic-legacy.schema.json`，不能作为标准合同样例。
`references/diagnostic-output.schema.json` 和 `references/report-template.md` 仅保留为 Legacy
兼容资料，后续阶段才允许迁移或退出。
