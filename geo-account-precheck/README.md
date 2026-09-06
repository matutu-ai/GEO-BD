# GEO-BD / GEO Diagnostic Engine V2

GEO-BD 是一套结构化 GEO Diagnostic Engine。它读取企业真实资料，把资料变成可追溯的事实、证据、实体与 AI 认知记录，再计算 EEAAP、EEAT、Scenario、Keyword、Citation、NAP 与九维加权 GEO Score，最后输出 P0/P1/P2/P3 诊断和行动计划。

它不是普通的企业资料分析：普通分析只总结“客户有什么”，GEO-BD 还会回答“AI 知道什么、推荐谁、为什么缺席、缺哪类证据、下一轮怎么复测”。没有真实数据时，输出必须是 `UNKNOWN` / `NOT_RUN` / `INSUFFICIENT_DATA`，禁止用推测或模拟结果冒充真实检测。

## 为什么需要 Engine

- 企业事实必须区分 `FACT / INFERENCE / UNKNOWN`，每条事实尽量带来源。
- AI 认知必须来自真实 `observed/provided` 回答；模拟回答永不参与评分。
- 竞品、Evidence、Citation 都需要来源与状态，不能自动编造。
- 每个分数要可追溯到实体字段、Evidence、Query 或 AI Test，而不是一句“整体还行”。
- 同一批 Query 用于 Before/After，复测结果才能做对比。

## 架构

```text
企业资料
  -> CompanyProfile / Entity
  -> Evidence Graph + Verification
  -> AI Cognition + Query Matrix
  -> Competitor Gap
  -> EEAAP / EEAT
  -> Scenario / Keyword / Citation / NAP
  -> GEO Scorecard
  -> GEO Gap -> Opportunity -> P0/P1/P2/P3 Action Plan
  -> Validation Plan -> 真实复测 -> Before/After Comparison
```

代码入口在 [engine/pipeline.py](engine/pipeline.py) 的 `DiagnosticPipeline`。主要模块：

```text
engine/
  pipeline.py              端到端编排
  entity/researcher.py     企业实体结构化
  evidence/                证据图与核验评分
  cognition/               AI 认知与 Query 生成
  query/                   Query Matrix / Intent
  competitor/              竞品状态与差距
  eeaap/ eeat/             EEAAP / EEAT 评分
  summary/                 Scenario/Keyword/Citation/NAP
  ai_test/                 AI Test 统计
  gap/ analyzer.py         GEO Gap
  scoring/opportunity.py   Opportunity Score
  recommendation/planner.py Action Plan
  validation/              Schema 校验与 Before/After
  scorecard.py             九维 GEO Score
  reports/generator.py     Markdown 报告
```

## 输入格式

V2 输入是 JSON 对象。`python scripts/run_diagnostic.py --template` 会输出 `inputs/diagnostic-template.json` 的完整模板。常用顶层字段：

```json
{
  "company": {
    "name": "公司全称",
    "aliases": [],
    "brands": [],
    "business": "主营业务",
    "industry": [],
    "products": [],
    "services": [],
    "customers": [],
    "cases": [],
    "locations": [],
    "founders": [],
    "experts": [],
    "certificates": [],
    "patents": [],
    "media": [],
    "website": "官网",
    "contacts": "联系方式",
    "reviews": [],
    "negative_information": []
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

用户提供的资料会被记为 `FACT`，来源是 `user_provided`，`verified=false`，不会冒充已联网核验。没有来源的 Evidence 会变成 `UNKNOWN`，不能因为输入里写了 `FACT` 就保留。

## 输出格式

`diagnostic.json` 顶层包含 20 个块：

`meta`、`company`、`entity`、`ai_cognition`、`query_matrix`、`competitors`、`evidence_graph`、`eeaap`、`eeat`、`gaps`、`opportunities`、`recommendations`、`validation`、`scores`、`data_quality`、`scenarios`、`keywords`、`citations`、`nap`、`ai_tests`。

Markdown 报告固定 19 个章节：

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

## GEO Score

GEO Score 是诊断指标，不是 AI 排名保证。它按九个维度加权，缺失维度不按 0 计算：

| 维度 | 权重 |
|---|---:|
| Entity | 10% |
| AI Cognition | 15% |
| Evidence | 20% |
| EEAAP | 15% |
| EEAT | 10% |
| Scenario | 10% |
| Keyword | 5% |
| Citation | 10% |
| NAP/Trust | 5% |

可计算维度不足一半时整体是 `INSUFFICIENT_DATA`。所有数值都保留在 `scores.basis`，说明来自哪个证据或观察。

## AI Cognition

`ai_observations` 里只接受真实 `observed` 或 `provided` 记录。每条记录可包含 query、query_type、是否 Mention/Recommendation/Citation、正确描述、Position、回答来源与原文理由。`simulated`、`raw` 或 `unknown` 不参与评分，认知保持 `UNKNOWN`。

## Evidence

Evidence 至少包含 claim、type/status、source、source_url、source_type、date、confidence、entity_match、verifiable、conflicts_with。核验检查来源、日期、第三方/独立来源、已验证、冲突和夸张/绝对化表述。`EvidenceVerifier` 没有 Evidence 时返回 `UNKNOWN`，只有可评分记录才算分。

## Competitor Gap

竞品必须是用户确认或真实观察得到的 `confirmed` 记录，不能由引擎自动发明。没有竞品时输出 `UNKNOWN` 和空列表。竞品差距只比较有真实数据支撑的维度。

## Scenario / Keyword / Citation / NAP

- Scenario Coverage：真实 AI 观察覆盖目标商业场景的比例。
- Keyword Coverage：真实 AI 观察覆盖意图的比例。
- Citation/Mention：真实 AI Test 中引用企业来源、提及和推荐的占比；没有真实 AI Test 时是 `NOT_RUN`，不产生数字。
- NAP：Name/Address/Phone 已知度与一致性；缺失或冲突时按不足处理。

## Diagnosis 与 Action Plan

`gaps` 输出可解释的缺口，`opportunities` 给出 Opportunity Score，`recommendations` 把 P0/P1/P2/P3 转成可执行任务、所需资料和验证方法。P0 是资料/证据/NAP 等基线问题，P1-P3 按业务价值、AI 需求、竞品差距、证据可得性和执行可行性排序。

## CLI

新用户从 [examples/00-quickstart.md](examples/00-quickstart.md) 开始，先用
[examples/01-quickstart.json](examples/01-quickstart.json) 跑通一轮，再看
[examples/02-answer-sheet.md](examples/02-answer-sheet.md) 学会读结果。

从仓库内 `geo-account-precheck/` 目录运行：

```bash
# 查看输入模板
python3 scripts/run_diagnostic.py --template

# 只打印一屏结论，不写任何文件
python3 scripts/run_diagnostic.py \
  --input examples/01-quickstart.json \
  --summary \
  --offline

# 完整 Demo：输入 JSON -> Markdown + diagnostic.json
python3 scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --output reports/diagnostic.md \
  --json reports/diagnostic.json \
  --needs-input reports/needs-input.md \
  --offline

# 下一轮：保留静态企业资料，清空旧观察/竞品/Evidence/指标
python3 scripts/prepare_round.py \
  --from reports/diagnostic.json \
  --out inputs/round2.json

# 兼容别名 run_diagnosis.py
python3 scripts/run_diagnosis.py \
  --input tests/fixtures/sample_company.json \
  --output reports/diagnostic.md \
  --json reports/diagnostic.json \
  --offline

# 单独分析真实 AI Test
python3 scripts/run_ai_test.py \
  --tests path/to/ai-test.json \
  --output reports/ai-test-result.json

# Before / After 对比
python3 scripts/compare_reports.py \
  --before reports/before.json \
  --after reports/after.json \
  --output reports/comparison.md

# 校验报告 Schema
python3 scripts/validate_diagnostic.py \
  --input reports/diagnostic.json
```

只要命令写了输出文件（Markdown/JSON/待补清单）或加了 `--summary`，终端就会先给出一屏结论：`GEO Score`、Top 行动、Evidence、Missing、AI Test，不用打开完整报告。

参数：`--input` 读输入 JSON；`--output` / `--markdown` 写 Markdown；`--json` 写结构化报告；`--summary` 只打印一屏摘要；`--needs-input PATH` 额外写出待补资料清单；`--check` 在数据不足时返回非零退出码；`--offline` 不联网且不虚构研究结果；`--research-mode` 支持 `manual/provided/external/offline`。

## 测试

项目没有第三方依赖，使用标准库测试：

```bash
python3 -m unittest discover -s tests -v
```

当前测试覆盖 Entity、Evidence、FACT/INFERENCE/UNKNOWN、EEAAP、EEAT、Competitor、Scenario、Keyword、AI Test、Citation、Score、Missing Data、Diagnosis、Schema、Before/After、CLI、下一轮输入准备与旧版 `generate_precheck.py`，共 81 项。

## 与旧版本兼容

- `scripts/generate_precheck.py` 保持不变，继续支持 GEO/讯灵账户前置背调、画像关键词与 AI 效果问题排查。
- 旧的 `--template / --input / --output / --audit / --checklist / --check` 用法不变。
- V2 主入口是 `run_diagnostic.py`，`run_diagnosis.py` 是兼容别名。
- `references/source-doc.md` 继续保留为 Legacy Operational Knowledge；评分只在有真实数据时使用运营经验作为启发，不把 20 篇、60-80 篇、7-15 天等数值写成 Guaranteed Rule。

## 完整 Demo

用 [tests/fixtures/sample_company.json](tests/fixtures/sample_company.json)（显式标注为虚拟测试样本）运行：

```bash
python3 scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --output reports/diagnostic.md \
  --json reports/diagnostic.json \
  --offline
python3 scripts/validate_diagnostic.py --input reports/diagnostic.json
```

生成的 `reports/diagnostic.json` 关键字段示例如下：

```json
{
  "meta": {"engine": "GEO Diagnostic Engine", "version": "2.0.0"},
  "entity": {"fields": {"name": [{"status": "FACT", "source_type": "user_provided"}]}},
  "ai_cognition": {"status": "OBSERVED", "count": 1},
  "query_matrix": {"coverage": {}},
  "evidence_graph": {"items": []},
  "eeaap": {},
  "eeat": {},
  "gaps": {},
  "opportunities": {},
  "recommendations": {"actions": []},
  "scenarios": {},
  "keywords": {},
  "citations": {},
  "nap": {},
  "ai_tests": {},
  "scores": {"geo_score": 83, "status": "COMPUTED"},
  "data_quality": {"score": 84}
}
```

`reports/diagnostic.md` 会按 19 个章节输出 GEO Score、Entity、AI Cognition、Evidence、EEAAP、EEAT、Competitor Gap、Scenario/Keyword/Citation/NAP、P0/P1/P2/P3 与复测计划。

真实客户上线时，请把 `ai_observations`、`competitors`、`evidence` 换成真实回答与来源；缺少的部分保持 `UNKNOWN` / `NOT_RUN`，不要编造数字。
