---
name: geo-bd-diagnostic-skill
description: 企业 AI 搜索可见度诊断与 GEO 增长处方：基于官网、资料、真实 AI 观察、Evidence 与竞品数据，诊断企业被 AI 理解、信任和推荐的缺口，并交接给后续 GEO 执行；不负责内容生产或长期运营。
---

# GEO-BD V3

## Purpose

企业 AI 搜索可见度诊断与增长处方引擎。它诊断企业当前 AI 认知状态、问题原因和优化优先级，并将结构化处方交接给后续 GEO Skill。

输出：企业定位诊断、AI 认知评分、EEAT 信任评分、GEO 缺口地图和增长处方。

这个 Skill 是 GEO 生态的诊断入口。它只负责回答“企业当前是什么状态、AI 怎么理解、为什么不被推荐、下一步先优化什么”，结果交给后续 GEO Strategy 和 GEO Production 使用。

## 快速执行

先把客户输入归并为一份结构化资料，再复用同一份事实完成所有评分、缺口和处方；不要让多个 Agent 重复读取官网、产品、案例和资质。

1. 只抽取能追溯来源的企业事实；未知资料直接标记 `UNKNOWN`。
2. 只将 `observed/provided` AI 观察写入 AI 可见度、推荐和 Query 评分；`simulated/unknown` 仅可用于设计复测问题。
3. 由同一诊断结果依次生成 AI Visibility、EEAT、GEO Gap 和 Growth Prescription，不重新研究企业或扩展到 GEO 执行层。
4. 默认输出运营摘要与结构化 JSON；仅在运营人员需要溯源时展开九部分完整报告。

这条路径优先保证读取少、输出短、事实可追溯。

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
  -> AI Visibility / EEAT / GEO Gap
  -> Growth Prescription
  -> GEO Diagnostic Report
```

1. 企业资料采集与定位：识别企业是谁、卖什么、服务谁、解决什么问题、可证明的选择理由。
2. AI 可见度：只用真实 AI 观察检测 `UNKNOWN -> KNOWN -> UNDERSTAND -> TRUST -> RECOMMEND`。
3. 信任与缺口：评分 EEAT，识别定位、场景、案例、信任、引用和专业表达缺口。
4. 增长处方：按问题、原因、影响和优先级交接 30/60/90 天能力建设方向。

诊断报告之后的运营交接由 `AIVisibilityAgent -> EEATTrustAgent -> GEOGapAgent -> DiagnosisAgent -> PrescriptionAgent` 完成：输出企业当前 AI 认知、信任评分、增长缺口和能力模块处方，不进入 GEO 执行层，不生成关键词、画像、内容标题或发布排期。`growth_prescription.json` 是后续 GEO Skill 的结构化输入。

## 默认输出

`python3 main.py` 或 `python3 geo-account-precheck/main.py` 生成：

- `GEO_AI诊断报告.md`
- `企业定位分析.md`
- `GEO缺口地图.md`
- `EEAT评分报告.md`
- `竞争分析.md`
- `GEO优化处方.md`
- `ai_visibility.json`、`eeat_score.json`、`geo_gap.json`、`growth_prescription.json`

对运营人员，先给出四项结论：当前 AI 阶段、最大问题、P0/P1 任务、下一次复测条件。完整九部分报告保留用于溯源，不以冗长叙述替代结构化字段。

## 交互提示层

`geo-account-precheck/interaction/` 提供按诊断节点调用的用户提示：`welcome`、`intake`、`diagnosis`、`competition`、`visibility`、`personas`、`prescription`、`report`。通过 `interaction.render_prompt(stage, context)` 渲染；未提供的动态字段统一显示 `【需企业补充真实资料】`。

交互层只解释当前节点、展示已知结果和引导下一步，不重新分析、不虚构排名，也不越过 GEO-BD 与 GEO 执行层的边界。

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
