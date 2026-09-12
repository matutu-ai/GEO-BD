# Agent 操作说明

这是 `matutu-ai/GEO-BD` 的核心代码目录 `geo-account-precheck/`。

## 学习顺序

1. 先读同目录 `README.md` 与 `SKILL.md`；上一级 `LEARN.md` 提供完整阅读顺序与模块地图。
2. 用虚拟样本跑通一次：`python3 scripts/run_diagnostic.py --input tests/fixtures/sample_company.json --summary --offline`。
3. 需要改某个领域时，先读该领域 package、对应 `schemas/*.json` 与对应 `tests/test_*.py`，不要一次加载全部文档。

## 核心不变式

- 企业资料默认记为 `FACT` 且 `verified=false`；没有数据必须输出
  `UNKNOWN / NOT_RUN / INSUFFICIENT_DATA`，禁止虚构结果。
- `simulated/unknown` AI 观察永不参与评分。
- 竞品需要真实 `candidate/confirmed` 记录，Evidence 必须有来源；不能自动发明。
- `diagnostic.json` 保留 V2 20 块结构；`report.json` 是 V3 `ReportModel`，
  报告层不重新计算业务指标。
- 旧 `generate_precheck.py`、`run_diagnosis.py`、`engine/reports/generator.py`
  是兼容入口，不要删除。

## 修改与验证

- 改代码后至少运行对应测试：`python3 -m pytest -q tests/目标文件`。
- 改动 JSON 结构时必须同步 schema 与报告测试。
- 全量基线：`python3 -m pytest -q`（121 passed）。
- `reports/` 下的生成产物与客户资料不得提交；真实客户数据不放进测试用例。
