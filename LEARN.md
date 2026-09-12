# GEO-BD 学习路径（给 AI 与新维护者）

目标：用最少阅读量掌握这个库，知道“改哪里、怎么验证、哪些不能碰”。
仓库内的完整实现位于 `geo-account-precheck/`。本文件在仓库根，后续路径写全
`geo-account-precheck/` 前缀；运行时命令请先 `cd geo-account-precheck`。

## 1. 最短阅读顺序（约 10 分钟）

先完整读两个入口文件，再按依赖方向读代码：

1. [geo-account-precheck/README.md](geo-account-precheck/README.md)：先懂产品、输入输出、三层报告与 CLI。
2. [geo-account-precheck/SKILL.md](geo-account-precheck/SKILL.md)：先懂“什么时候使用、执行流程、严禁虚构”。
3. [geo-account-precheck/examples/00-quickstart.md](geo-account-precheck/examples/00-quickstart.md)：跑通一条真实命令，并对照
   [geo-account-precheck/examples/02-answer-sheet.md](geo-account-precheck/examples/02-answer-sheet.md) 理解终端摘要。
4. `geo-account-precheck/engine/models/`：读 `company/entity/evidence/query/cognition/report` 等数据类，
   它们是后续所有函数的契约。入口见 `geo-account-precheck/engine/models/__init__.py`。
5. `geo-account-precheck/engine/pipeline.py`：只读 `DiagnosticPipeline.run()` 一节，按函数调用顺序
   理解“资料如何变成 20 块 `DiagnosticResult`”。
6. `geo-account-precheck/engine/reporting/generator.py` 与
   `geo-account-precheck/engine/reporting/models.py`：理解 V3 为什么
   把“算诊断”与“讲报告”拆开；`report.json` 是共享 `ReportModel`。
7. `geo-account-precheck/tests/test_end_to_end.py`、`test_cli.py`、`test_schema.py`：
   把“入口命令、JSON 契约、合法边界”一次看齐。

需要改某一领域时，按“该领域 package -> 对应 schema -> 对应测试”三角读：
例如改竞品就依次读 `geo-account-precheck/engine/competitor/`、
`geo-account-precheck/schemas/competition-intelligence.schema.json`、
`geo-account-precheck/tests/test_competitor.py`。

## 2. 模块地图

```text
geo-account-precheck/engine/
  pipeline.py                 唯一端到端编排入口；先读 run()
  models/                     数据契约（先读）
  providers.py                未来外部研究/AI 查询接口；offline 模式永不虚构
  entity/researcher.py        企业实体结构化，FACT/INFERENCE/UNKNOWN
  cognition/analyzer.py       AI 认知（只统计真实 observed/provided）
  query/                      意图分类与 Query Matrix
  evidence/                   证据图与核验
  competitor/                 竞品认知与差距（candidate/confirmed）
  eeaap/ eeat/                EEAAP / EEAT 评分
  summary/                    Scenario / Keyword / Citation / NAP
  gap/ scoring/ recommendation/ 缺口 -> Opportunity -> P0/P1/P2/P3
  validation/                 Schema 校验与 Before/After
  scorecard.py                九维 GEO Score
  enterprise_intelligence/     背调 + 条件式推荐引擎（V3 新层）
  reporting/
    insight_engine.py          DiagnosticResult -> ReportModel 的结论整理
    models.py                  ReportModel
    generator.py               分层报告入口
    executive_renderer.py      L1（默认）
    operational_renderer.py    L2
    technical_renderer.py      L3（复用旧 19 章节）
  reports/generator.py         旧 V2 render_markdown() 兼容层，新代码不依赖它

geo-account-precheck/schemas/                    每个数据块一份 JSON Schema
geo-account-precheck/scripts/run_diagnostic.py   V3 主命令
geo-account-precheck/scripts/generate_precheck.py  旧前置背调命令，保持兼容
```

## 3. 两个 JSON 的关系

- `diagnostic.json`：`DiagnosticResult` 的 20 个原始诊断块（V2 兼容）。
- `report.json`：`InsightEngine` 整理后的 V3 `ReportModel`，供三层渲染共享。
- 业务指标只在 Pipeline 层计算；报告层不重算，只做取舍与排版。
- `competition_intelligence` 挂在 `DiagnosticResult` 内，对应
  `geo-account-precheck/schemas/competition-intelligence.schema.json`，由
  `geo-account-precheck/engine/enterprise_intelligence/engine.py` 输出。

## 4. 测试速查

无第三方依赖：

```bash
cd geo-account-precheck
python3 -m pytest -q                                        # 全量 121 项
python3 -m pytest -q tests/test_competitor.py               # 只跑目标模块
python3 -m pytest -q tests/test_end_to_end.py tests/test_schema.py
python3 -m unittest discover -s tests -v
```

改动与测试对应关系：

```text
pipeline 数据流        test_end_to_end / test_diagnostic_boundaries
report 分层            test_executive_report / test_operational_report /
                       test_technical_report / test_insight_engine
背调 + 条件推荐         test_dezhou_tuosheng / test_opportunity_engine
旧命令兼容             test_generate_precheck / test_cli
```

## 5. 可以跳过的内容

首次学习不需要完整读：`geo-account-precheck/references/`（旧运营知识底稿）、
`geo-account-precheck/engine/reports/`（V2 兼容层）、
`geo-account-precheck/inputs/diagnostic-template.json`、
`geo-account-precheck/tests/cases/dezhou-tuosheng`（真实企业回归样本，仅用于测试）、
生成产物目录 `geo-account-precheck/reports/`。

## 6. 修改约定

- 不编造企业事实、AI 推荐结果、竞品或来源；`simulated` 观察永不参与评分。
- 先读目标领域的数据类与 schema，再改逻辑；改输出结构必须同步 schema 和测试。
- 保持 `UNKNOWN / NOT_RUN / INSUFFICIENT_DATA` 语义，缺失维度不得按 0 计算。
- 新命令走 `run_diagnostic.py`，保留 `run_diagnosis.py` 兼容别名。
- 提交前跑对应领域测试；全量基线是 121 passed。
