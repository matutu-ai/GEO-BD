# GEO-BD 最短学习路径

目标：先掌握“内部可追溯、外部一页看懂”的唯一产品边界，再阅读当前实现。不要把
现有旧代码的复杂度反向定义成产品职责。

## 1. 先读边界与合同

按以下顺序阅读：

1. 根目录 `README.md`：产品边界与迁移状态。
2. `geo-account-precheck/AGENTS.md`：不可破坏的工程约束。
3. `geo-account-precheck/schemas/diagnostic.schema.json`：唯一标准合同。
4. `skills/geo-bd-diagnostic-skill/references/diagnostic-contract.md`：字段、状态和引用链说明。
5. 两份 `SKILL.md`：使用方式与职责边界。
6. `geo-account-precheck/tests/test_product_boundary_contract.py`：可执行边界。

只有在需要审计或进入后续改造阶段时，才继续读 `engine/pipeline.py`、领域模块和
Reporting。阶段 0 不以旧 Pipeline 输出作为标准合同样例。

## 2. 唯一标准主链

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

模块责任：

| 阶段 | 允许做什么 | 禁止做什么 |
|---|---|---|
| Facts | 保存客户输入或公开事实及来源 | 把推测写成事实 |
| Evidence Verification | 核验事实并记录冲突 | 因为出现关键词就判定已核验 |
| Diagnostic Measurements | 基于事实和证据计算指标 | 用默认分填补缺失数据 |
| Judgments | 引用 Fact/Metric 作出诊断判断 | 无依据生成结论 |
| Root Causes | 引用 Judgment 定位根因 | 把建议冒充根因 |
| Prescriptions | 引用 Root Cause 开能力处方 | 生成关键词、内容或运营排期 |
| Report Projection | 投影一页快速诊断 | 重算、生成 Gap、展示内部技术结构 |

对外只允许五段：客户定位、AI/GEO 状态、最多 5 条主要问题、P0/P1/P2 优化方向、
3—5 条关键诊断依据。Facts、Evidence、Measurements、Judgments、Root Causes 和
Prescriptions 是内部推理链，不直接展示给最终用户。

## 3. GEO 与 GEO-BD

```text
GEO-BD：事实 → 判断 → 根因 → 处方
GEO：关键词 → 画像 → 内容 → 发布 → 运营 → 复测执行
```

外部提供的真实测试 Query 可以作为 `PROVIDED` 或 `OBSERVED` 输入事实；GEO-BD
不得自动生成目标市场 Query。复测执行本身属于 GEO，GEO-BD只能定义验证条件和
读取复测结果。

## 4. 统一状态

唯一状态集合：

```text
VERIFIED
OBSERVED
PROVIDED
INFERRED
UNKNOWN
NOT_RUN
INSUFFICIENT_DATA
```

`UNKNOWN`、`NOT_RUN`、`INSUFFICIENT_DATA` 的指标值必须为 `null`。不再使用
`FACT`、`INFERENCE`、`DERIVED`、`ESTIMATED` 或中文占位词作为机器状态。

## 5. 当前实现与标准的关系

- `schemas/diagnostic.schema.json`：唯一标准合同。
- `schemas/diagnostic-legacy.schema.json`：当前旧 Pipeline 的兼容合同。
- `engine/pipeline.py`：当前实现，阶段 0 不修改；不能据此扩大产品边界。
- `engine/reporting/`：当前仍含诊断计算，阶段 0 仅记录违规，不修改。
- `engine/enterprise_intelligence/`、`engine/summary/`、旧前置背调脚本：当前保留，
  但不是标准 GEO-BD 职责。
- `geo-account-precheck-rs/`：未跟踪的平行实现，本阶段禁止修改。

## 6. 测试路由

阶段 0 先运行：

```bash
cd geo-account-precheck
python3 -m pytest -q tests/test_product_boundary_contract.py
```

再运行全量回归：

```bash
python3 -m pytest -q
```

旧 Pipeline 测试必须显式使用 `diagnostic-legacy.schema.json`。任何新标准输出都必须
通过 `diagnostic.schema.json` 和引用完整性测试。

## 7. 本阶段不可进入的工作

不得修改 Pipeline、评分、Gap、Reporting 实现、Rust 工程；不得迁移或删除旧模块。
这些工作属于后续阶段，不能因阶段 0 测试暴露违规而提前修复。
