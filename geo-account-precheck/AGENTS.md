# GEO-BD Agent 操作规范

本目录是 `matutu-ai/GEO-BD` 的 Python 工程。实际代码行为不得反向覆盖本文件定义的
产品边界；若实现与合同冲突，应明确记录为待迁移违规。

## 唯一职责

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

```text
GEO-BD：事实 → 判断 → 根因 → 处方
GEO：关键词 → 画像 → 内容 → 发布 → 运营 → 复测执行
```

GEO-BD 禁止自动生成关键词、画像、内容、发布计划、媒体投放计划、目标市场 Query、
固定 30/60/90 天运营计划，也不承担 GEO 执行和复测执行。

对外产品只能输出一页《客户 GEO 快速诊断》：客户定位、AI/GEO 状态、最多 5 条
主要问题、P0/P1/P2 优化方向、3—5 条关键依据。不得向最终用户展示内部评分体系、
Gap 体系、Agent 过程、Schema、完整 JSON 或内部引用链。

## 唯一合同

- 标准合同：`schemas/diagnostic.schema.json`。
- 旧输出兼容合同：`schemas/diagnostic-legacy.schema.json`。
- 新字段不得加入 Legacy 合同后再宣称为标准。
- 标准顶层必须包含并分离 `facts`、`judgments`、`root_causes`、
  `prescriptions`。

引用链是硬约束：

- Judgment 至少引用一个存在的 Fact ID 或 Diagnostic Metric ID。
- Root Cause 至少引用一个存在的 Judgment ID。
- Prescription 至少引用一个存在的 Root Cause ID。
- 没有完整引用链时不得输出判断、根因或处方。

## 统一状态语义

机器状态只允许：

- `VERIFIED`：已经过明确核验方法和可追溯来源确认。
- `OBSERVED`：直接观察到，但不代表已经独立核验。
- `PROVIDED`：由客户或上游提供，尚未独立核验。
- `INFERRED`：由可引用事实或指标推导，不得写入 Facts。
- `UNKNOWN`：当前不知道；相关值必须为 `null`。
- `NOT_RUN`：该检查没有执行；相关值必须为 `null`。
- `INSUFFICIENT_DATA`：已尝试但数据不足；相关值必须为 `null`。

禁止新增 `FACT`、`INFERENCE`、`DERIVED`、`ESTIMATED` 等平行机器状态。旧代码中的
这些值属于阶段 1 以后需要迁移的已知违规。

## 分层约束

- 领域层才能形成 Diagnostic Measurement、Judgment、Root Cause 和 Prescription。
- Reporting 只能按 ID 读取并投影已有结果，不得重新评分、生成 Gap、设置业务优先级
  或产生新的业务判断；`report_projection` 是唯一用户可见合同。
- Template 与 Prompt 只能定义展示格式和采集问题，不能预设企业问题、固定处方或
  运营周期。
- 外部提供的测试 Query 可作为输入事实；系统不得生成目标市场 Query。

## 修改前阅读

1. 上一级 `README.md` 与 `LEARN.md`。
2. 本目录 `README.md` 与两份 `SKILL.md`。
3. `schemas/diagnostic.schema.json`。
4. `tests/test_product_boundary_contract.py`。
5. 仅在任务需要时读取目标 package、对应 schema 和测试。

## 阶段 0 保护范围

阶段 0 只允许修改规范、Schema、文档和产品边界测试。不得修改：

- `engine/pipeline.py`
- 评分算法
- Gap 算法
- Reporting 实现
- `geo-account-precheck-rs/`
- 旧模块和兼容入口

旧 `generate_precheck.py`、`run_diagnosis.py`、`engine/reports/generator.py` 暂时保留，
但不得作为新标准能力引用。

## 验证

```bash
python3 -m pytest -q tests/test_product_boundary_contract.py
python3 -m pytest -q
```

报告测试结果时必须区分标准合同验证和 Legacy 回归。不得因为 Legacy 测试通过就宣称
当前 Pipeline 已符合标准合同。
