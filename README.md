# GEO-BD / GEO Diagnostic Engine

企业 GEO 诊断引擎仓库。核心代码与文档都放在
[geo-account-precheck/](geo-account-precheck/)：

- 读取企业资料、真实 AI 观察、竞品与 Evidence；
- 生成可追溯的 Entity、Evidence Graph、AI Cognition、Query Matrix 与九维 GEO Score；
- 输出 P0/P1/P2/P3 诊断、行动计划和复测方案；
- 报告层使用 `DiagnosticResult -> InsightEngine -> ReportModel -> Renderer` 分成三层视图。

没有真实数据时输出必须保持 `UNKNOWN / NOT_RUN / INSUFFICIENT_DATA`，禁止用推测结果冒充真实检测。

## 从这里开始

1. [geo-account-precheck/README.md](geo-account-precheck/README.md)：完整产品说明、输入输出、CLI 参数与 Demo。
2. [geo-account-precheck/SKILL.md](geo-account-precheck/SKILL.md)：技能入口；记录“什么时候使用、执行流程、严禁虚构”。
3. [LEARN.md](LEARN.md)：给其他 AI/新维护者按阅读顺序准备的模块地图，用于快速掌握代码结构。
4. 最快跑通一条命令：

```bash
cd geo-account-precheck
python3 scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --report-level all \
  --output /tmp/geo-v3-demo \
  --offline
```

诊断 Skill 的专用入口见 [skills/geo-bd-diagnostic-skill/SKILL.md](skills/geo-bd-diagnostic-skill/SKILL.md)，Golden Test Case 001 见 [geo-account-precheck/tests/cases/case_001_tuoshi_ventilation/](geo-account-precheck/tests/cases/case_001_tuoshi_ventilation/)。

## 目录地图

```text
geo-account-precheck/
  README.md        完整说明（产品视角）
  SKILL.md         Skill 入口
  scripts/         CLI 与兼容脚本
  engine/          引擎：pipeline、models、scoring、reporting 等
  schemas/         输入/结果 JSON Schema
  tests/           标准库测试与回归用例
  examples/        虚拟示例与速查表
  inputs/          输入模板
  references/      运营知识底稿（Legacy）
```

修改代码前请先阅读 `LEARN.md`，确定只改目标模块并运行对应测试；不要把
`reports/` 下的生成物或真实客户资料提交进仓库。
