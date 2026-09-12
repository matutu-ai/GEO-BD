---
name: geo-diagnostic-engine
description: 执行企业 GEO 全链路诊断，包括企业实体研究、AI 认知分析、Query Matrix、竞品认知、Evidence Graph、EEAAP/EEAT 评分、GEO Gap、Opportunity Score、优化任务和复测；同时保留 GEO/讯灵账户前置背调、画像关键词与 AI 推荐效果排查能力。当用户要求 GEO 诊断、实体/认知/竞品/证据/机会/推荐/复测，或讯灵账户画像自查与效果排查时使用。
---

# GEO Diagnostic Engine V3

> 学习顺序：先读本文件掌握“什么时候用、执行流程、严禁虚构”，再读 `README.md`
> 掌握输入输出与 CLI；需要了解代码模块时读上一级 `LEARN.md` 的文件地图，不要一次
> 加载全部 engine/schemas/tests。最快验证命令：
> `python3 scripts/run_diagnostic.py --input tests/fixtures/sample_company.json --summary --offline`

面向优化前诊断的独立 Skill 入口是上一级 `skills/geo-bd-diagnostic-skill/SKILL.md`；Golden Test Case 001 位于 `tests/cases/case_001_tuoshi_ventilation/`。

本 Skill 把 GEO-BD 从“前置背调 + 固定规则报告生成器”升级为可运行、可测试、可扩展的 GEO 诊断引擎。V3 数据流固定为 `DiagnosticPipeline -> DiagnosticResult -> InsightEngine -> ReportModel -> Executive/Operational/Technical Renderer`：底层继续算完整指标，报告层负责决定用户第一屏看到什么。

原有 V2 Engine、Evidence Graph、Query Matrix、AI Observation、Competitor、Scoring、Recommendation 与 `generate_precheck.py` 全部能力继续保留。`run_diagnostic.py` 默认输出 V3 Executive Report，`--legacy-report` 可回退到旧 V2 19 章节 Markdown。

## 什么时候使用

- 需要回答“AI 知道客户什么、不知道什么、为什么推荐竞品而不是客户”。
- 需要把客户资料变成企业实体、Evidence Graph、Query Matrix 和竞品差距。
- 需要知道客户在哪些搜索问题中缺席、缺什么证据、最大 GEO 差距在哪里。
- 需要按机会优先级得到 P0/P1/P2/P3 行动清单和复测方法。
- 需要旧的 GEO/讯灵前置背调、九大画像自查、EEAAP/EEAT 检测或 AI 效果问题排查。

## 输入

V3 继续兼容 V2 输入，使用自然的客户资料 JSON，至少可以包含：

```json
{
  "company": {
    "name": "公司全称",
    "aliases": ["公司别名"],
    "brands": ["品牌名"],
    "business": "主营业务",
    "industry": ["行业"],
    "products": ["产品"],
    "services": ["服务"],
    "customers": ["目标客群"],
    "cases": ["真实客户案例"],
    "locations": ["地域"],
    "founders": ["创始人"],
    "experts": ["专家"],
    "certificates": ["资质"],
    "patents": ["专利"],
    "media": ["媒体报道"],
    "website": "官网",
    "contacts": "联系方式",
    "reviews": ["客户评价"],
    "negative_information": ["已核验负面信息"]
  },
  "materials": [],
  "ai_observations": [],
  "competitors": [],
  "evidence": [],
  "issues": [],
  "keyword_directions": [],
  "current_metrics": {},
  "validation": {},
  "constraints": {}
}
```

`python scripts/run_diagnostic.py --template` 会输出完整模板。用户不需要填写引擎内部字段，Engine 负责结构化。

## 输出

运行后得到分层 Markdown、`diagnostic.json` 与可选的 `report.json`。原始 `diagnostic.json` 顶层保留 V2 20 个诊断块：

`meta`、`company`、`entity`、`ai_cognition`、`query_matrix`、`competitors`、`evidence_graph`、`eeaap`、`eeat`、`gaps`、`opportunities`、`recommendations`、`validation`、`scores`、`data_quality`、`scenarios`、`keywords`、`citations`、`nap`、`ai_tests`。

V3 默认 `executive`：

- L1 `executive`：`# GEO诊断报告`，先给 Health Score 与一句话诊断，再给 Top 3 Problems、Top 3 Opportunities、Action Plan、复测指标与可信度说明。
- L2 `operational`：`# GEO Operational Report`，给 GEO/内容/增长团队展开 AI、Query Cluster、Competitor、Entity、Evidence、Opportunity 与 Action。
- L3 `technical`：`# GEO Diagnostic Report`，保留 V2 完整 19 章节原始诊断，给专家/技术人员/Agent。

`report.json` 是共享 ReportModel，顶层字段为 `meta`、`health`、`core_metrics`、`ai_cognition`、`top_problems`、`opportunities`、`action_plan`、`query_clusters`、`competitor_summary`、`entity_consistency`、`evidence_conflicts`、`baseline`、`measurement`、`evidence_refs`、`confidence`。

诊断结果同时包含 `final_summary`。它是只读归纳层，不重新分析或生成事实；`--report-level all` 会输出运营人员可直接阅读的 `geo_summary.md`。未知内容使用 `【需客户补充真实资料】`，受限业务不得被总结成企业定位。

L3 对应的旧 19 章节仍可用于完整技术视图：

1. Executive Summary
2. Company Entity
3. AI Cognition
4. Query Intelligence
5. Competitor Intelligence
6. Evidence Graph
7. EEAAP
8. EEAT
9. Scenario Coverage
10. Keyword Coverage
11. AI Test
12. NAP / Trust
13. GEO Gap
14. GEO Opportunity
15. P0/P1/P2/P3 Action Plan
16. Next Test
17. Validation Plan
18. Data Quality
19. Unknown / Missing Data

缺失数据处理原则不变：没有真实 AI Observation 时，AI 认知/推荐/引用与竞品 AI 指标必须输出 `UNKNOWN`；没有足够证据时 Evidence Strength 等指标不能假装算出来。`simulated` 观察永不参与评分。

## 执行流程

1. 读取客户资料并确认已有/缺失内容。
2. 将资料结构化为企业实体，逐条保留来源与 `FACT/INFERENCE/UNKNOWN`。
3. 建立 Evidence Graph，把声明、来源、日期、核验状态落到节点和边。
4. 检查当前 AI 认知，只用真实 `observed/provided` 观察。
5. 生成 Query Matrix 并分类意图。
6. 识别竞品，candidate 必须人工确认后才能作为事实。
7. 计算竞品差距。
8. 计算 EEAAP。
9. 计算 EEAT。
10. 计算 GEO Gaps。
11. 计算 Opportunity Score。
12. 生成 P0/P1/P2/P3。
13. 生成可执行任务和所需资料。
14. 生成复测计划。
15. 用 `InsightEngine` 生成 `ReportModel`。
16. 按需要渲染 Executive / Operational / Technical 分层报告。

## 第一原则：严禁虚构

- 企业信息、案例、参数、客户、资质、荣誉、电话、官网、负面舆情、AI 推荐结果、竞品和引用来源均不能编造。
- 用户提供的资料可以记为 `FACT`，来源为 `user_provided`，`verified=false`，不冒充已联网核验。
- 没有数据时必须输出 `UNKNOWN`，不能把猜测写成结论。
- `INFERENCE` 只能用于引擎基于已有输入生成的候选 Query、机会排序等内部推导。
- 模拟 AI 回答永不参与真实评分；`simulated/unknown` 观察会让认知和覆盖率保持 `UNKNOWN`。
- 没有可靠竞品时输出 `UNKNOWN`，不自动制造竞品；竞品需要 `candidate/confirmed` 状态与来源。
- Evidence 评分检查来源、日期、可核验性、第三方/第一方、冲突、过期、自述、夸张和绝对化表述。
- 没有真实 AI 测试结果时，Mention/Recommendation/Citation/Scenario/Keyword 覆盖率必须保持 `NOT_RUN` 或 `UNKNOWN`，不能拿生成 Query 的意图冒充覆盖率。

## 评分边界

所有分数都是可追溯的 Diagnostic Indicator，不是 AI 平台真实排名保证，也不承诺发布数量会带来固定效果。

- GEO Diagnostic Score：按 Entity 10%、AI Cognition 15%、Evidence 20%、EEAAP 15%、EEAT 10%、Scenario 10%、Keyword 5%、Citation 10%、NAP/Trust 5% 九维加权；缺失维度不按 0 计算。
- Data Quality Score：统计 FACT/INFERENCE/UNKNOWN、已核验/未核验、来源数、Evidence/Source/Verification Completeness。
- 数据质量低时报告必须提示“当前诊断结论可信度有限”。
- source-doc 里的 20 篇、60-80 篇、7 天、7-15 天、100/200/500 篇等是 Operational Heuristic，不是 Guaranteed Rule。

## 运行 V3

完整使用示例：

```bash
python scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --output reports/executive.md \
  --report-json reports/report.json \
  --offline
```

常用命令：

```bash
# 生成输入模板
python scripts/run_diagnostic.py --template

# 只打印一屏结论，不写文件
python scripts/run_diagnostic.py \
  --input examples/01-quickstart.json \
  --summary \
  --offline

# 生成 V3 Executive Report 与原始诊断 JSON
python scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --output reports/executive.md \
  --json reports/diagnostic.json \
  --needs-input reports/needs-input.md \
  --offline

# 三层报告：executive/operational/technical + diagnostic.json + report.json
python scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --report-level all \
  --output /tmp/geo-v3-demo \
  --needs-input reports/needs-input.md \
  --offline

# L2 Operational Report
python scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --report-level operational \
  --output reports/operational.md \
  --offline

# 旧 V2 19 章节完整 Markdown
python scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --legacy-report \
  --output reports/diagnostic.md \
  --offline

# 下一轮：保留静态企业资料，清空旧观察/竞品/Evidence/指标
python scripts/prepare_round.py \
  --from reports/diagnostic.json \
  --out inputs/round2.json

# run_diagnosis.py 是兼容别名；加 --legacy-report 可恢复旧 V2 Markdown
python scripts/run_diagnosis.py \
  --input tests/fixtures/sample_company.json \
  --legacy-report \
  --output reports/diagnostic.md \
  --json reports/diagnostic.json \
  --offline

# 单独分析真实 AI 测试记录
python scripts/run_ai_test.py \
  --tests inputs/ai-test.json \
  --output reports/ai-test-result.json

# 比较 Before/After 两轮诊断
python scripts/compare_reports.py \
  --before reports/before.json \
  --after reports/after.json \
  --output reports/comparison.md

# 数据不足时以非零退出码结束
python scripts/run_diagnostic.py \
  --input inputs/empty.json \
  --check

# 校验已有报告
python scripts/validate_diagnostic.py \
  --input reports/diagnostic.json
```

参数说明：

- `--report-level {executive,operational,technical,all}`：默认 `executive`；`all` 时一次生成三层 Markdown 与两份 JSON。
- `--output` / `--markdown`：写 Markdown；单层时是文件路径，`all` 时是目录。
- `--json PATH`：写原始 `diagnostic.json`（V2 20 块 `DiagnosticResult`）。
- `--report-json PATH`：写 V3 `report.json`（InsightEngine 生成的 `ReportModel`）。
- `--legacy-report`：强制输出旧 V2 19 章节 Markdown。
- `--check`：资料不足时返回非零退出码。
- `--template`：输出输入模板。
- `--offline`：不联网运行，缺失内容保持 `UNKNOWN`。
- `--research-mode`：`manual/provided/external/offline`，当前默认 `offline`。
- `--validate`：校验已有报告 JSON。
- `--summary`：只打印一屏 `GEO Score / Top / Evidence / Missing / AI Test`。
- `--needs-input`：把待补资料写成 Markdown 清单。
- `--final-summary PATH`：额外写出客户 GEO 情况总结；`all` 模式默认生成 `geo_summary.md`。

写文件命令默认在终端给出一屏摘要，完整报告见输出文件；`--summary` 可在不写文件时复用
同一屏摘要。新用户先读 `examples/00-quickstart.md`。

## 保留旧功能

`scripts/generate_precheck.py` 继续向后兼容：

```bash
python scripts/generate_precheck.py --template --output inputs.json

python scripts/generate_precheck.py \
  --input inputs.json \
  --output outputs/precheck.md

python scripts/generate_precheck.py \
  --input inputs.json \
  --audit \
  --output outputs/issue-audit.md

python scripts/generate_precheck.py --checklist

python scripts/generate_precheck.py --check
```

旧流程输出原有报告：资料自查、账户画像与关键词、EEAAP 检测、行动清单、电话/官网/NAP 排查。

## 数据与运行环境

当前没有接入真实搜索/AI API 时，引擎使用 `ManualProvider` 或 `OfflineProvider`。Provider 接口已经预留 `research_company/search_evidence/find_competitors/run_query/batch_run/verify`，未来可以接入 Web Search、豆包、ChatGPT、Gemini、Perplexity、企业知识库等，不需要改评分与报告逻辑。

运行前若客户没有给足资料、真实 AI 观察或竞品确认数据，先明确“当前不能生成哪些结论”，再补资料。复测必须使用同一批 Query 和真实观察，Before/After 缺失时 Validation 输出 `UNKNOWN`。

## 参考资料

[references/source-doc.md](references/source-doc.md) 保留为 Legacy Operational Knowledge：九大画像、EEAAP、EEAT、发布策略、训练策略、NAP 和效果排查规则都在其中。引擎优先真实数据、证据、AI 观察、Query 结果和竞品差距，再参考这些运营经验。
