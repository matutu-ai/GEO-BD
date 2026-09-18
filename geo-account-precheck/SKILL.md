---
name: geo-diagnostic-engine
description: 根据客户名称或基础资料快速生成一页企业 GEO 诊断，回答客户定位、当前 AI/GEO 状态、主要问题和 P0/P1/P2 优化方向。当用户需要快速判断客户现状和下一步方向时使用；不用于背调、关键词、画像、内容、发布或 GEO 运营执行。
---

# GEO Diagnostic Engine

## 目标

对外只回答四类问题：

1. 这家公司是谁，主要做什么，如何一句话定位？
2. AI 目前如何认知这家公司？
3. 当前最主要的 3—5 个问题是什么？
4. 下一步 P0/P1/P2 应优先优化什么方向？

输入可以只有客户名称，也可以是客户基础资料。内部事实不足时必须明确标记未知，不能
为了完成一页报告而补写结论。

## 固定边界

```text
GEO-BD：事实 → 判断 → 根因 → 处方
GEO：关键词 → 画像 → 内容 → 发布 → 运营 → 复测执行
```

不得生成关键词、画像、内容、发布计划、媒体投放计划、目标市场 Query 或固定
30/60/90 天运营计划。外部提供的真实测试 Query 可以作为输入事实，但本 Skill 不得
创造市场 Query。

## 标准工作流

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

按顺序执行，禁止跨阶段补结论：

1. 将客户输入和公开资料记录为带来源 ID 的 Facts。
2. 对需要核验的 Fact 记录方法、来源、结论和冲突。
3. 只从 Facts 和 Evidence 计算 Diagnostic Measurements。
4. Judgment 至少引用一个 Fact ID 或 Metric ID。
5. Root Cause 至少引用一个 Judgment ID。
6. Prescription 至少引用一个 Root Cause ID，只描述能力修复和验收方法。
7. Report Projection 只展示已有对象，不产生新判断。

Facts、Evidence、Measurements、Judgments、Root Causes 和 Prescriptions 是内部能力，
不直接堆给最终用户。

## 唯一对外格式

最终报告控制在一页左右，固定为：

```text
# 客户 GEO 快速诊断
一、客户定位
二、当前 AI / GEO 状态（2—4 句话）
三、当前主要问题（最多 5 条）
四、下一步优化方向（P0 / P1 / P2）
五、诊断依据（最关键的 3—5 条）
```

禁止展示多套评分、多套 Gap、九大画像、关键词矩阵、内容矩阵、30/60/90 天计划、
复杂技术字段、Agent 过程或大量 JSON。

## 唯一合同

标准输出必须通过 `schemas/diagnostic.schema.json`。标准顶层只有：

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

`report_projection` 是唯一用户可见部分。`schemas/diagnostic-legacy.schema.json` 仅用于
阶段迁移期间验证旧 Pipeline 产物，不是新输出合同。

## 统一状态

- `VERIFIED`：有核验方法和可追溯来源。
- `OBSERVED`：直接观察到，不等于独立核验。
- `PROVIDED`：客户或上游提供，未独立核验。
- `INFERRED`：由引用事实或指标推导；禁止写入 Facts。
- `UNKNOWN`：当前不知道，测量值必须为 `null`。
- `NOT_RUN`：检查未执行，测量值必须为 `null`。
- `INSUFFICIENT_DATA`：已尝试但数据不足，测量值必须为 `null`。

不得输出 `FACT`、`INFERENCE`、`DERIVED`、`ESTIMATED` 等平行机器状态。

## 报告约束

Reporting 和模板只能映射、分组、裁剪和格式化。禁止在报告层：

- 重新评分
- 生成 Gap
- 新增 Judgment、Root Cause 或 Prescription
- 重新设定优先级
- 生成任何 GEO 执行物

## 使用前检查

- 没有来源的输入不得标为 `VERIFIED`。
- 没有真实观察时，对应测量使用 `UNKNOWN` 或 `NOT_RUN`，值为 `null`。
- 没有完整引用链时，停止在最后一个有依据的阶段。
- 禁止用行业常识、默认分、模板文案或历史客户样例填补事实。

阶段 0 的完整字段和引用规则见上一级
`skills/geo-bd-diagnostic-skill/references/diagnostic-contract.md`。当前旧 Pipeline 尚未完成
合同迁移；不要把旧输出当作新合同示例。
