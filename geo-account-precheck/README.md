# GEO-BD Python Engine

GEO-BD 是轻量企业 GEO 快速诊断工具。输入客户名称或基础资料后，它内部形成可追溯
的事实、判断、根因和处方，对外只给一页、一眼能看懂的结果。它不是企业背调平台，
也不承担 GEO 执行。

## 产品边界

唯一标准流程：

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

GEO-BD 与 GEO 的职责固定为：

```text
GEO-BD：事实 → 判断 → 根因 → 处方
GEO：关键词 → 画像 → 内容 → 发布 → 运营 → 复测执行
```

GEO-BD 可以说明“缺少什么能力、为什么缺少、应修复什么能力、如何验收”，但不能
代替 GEO 生成关键词、画像、内容、发布计划、媒体投放计划、目标市场 Query 或运营
排期。

## 标准诊断合同

唯一标准 Schema：[`schemas/diagnostic.schema.json`](schemas/diagnostic.schema.json)。

标准顶层：

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

引用链：

```text
FACT-* / METRIC-* → JUDGMENT-* → ROOT-* → PRESCRIPTION-*
```

- Judgment 必须引用至少一个已存在的 Fact ID 或 Metric ID。
- Root Cause 必须引用至少一个已存在的 Judgment ID。
- Prescription 必须引用至少一个已存在的 Root Cause ID。
- Report Projection 只能引用并展示已有合同对象，不得生成新诊断。

完整字段说明见
[`../skills/geo-bd-diagnostic-skill/references/diagnostic-contract.md`](../skills/geo-bd-diagnostic-skill/references/diagnostic-contract.md)。

## 状态语义

| 状态 | 含义 | 允许阶段 |
|---|---|---|
| `VERIFIED` | 经过明确方法和可追溯来源核验 | Facts、Evidence Verification、Measurements、整体状态 |
| `OBSERVED` | 直接观察到，未必独立核验 | Facts、Measurements、整体状态 |
| `PROVIDED` | 客户或上游提供，未独立核验 | Facts、Measurements、整体状态 |
| `INFERRED` | 由已引用事实或指标推导 | Measurements、Judgments、Root Causes、Prescriptions、整体状态 |
| `UNKNOWN` | 当前不知道 | Facts、Evidence Verification、Measurements、整体状态 |
| `NOT_RUN` | 检查没有执行 | Evidence Verification、Measurements、整体状态 |
| `INSUFFICIENT_DATA` | 已尝试但数据不足 | Evidence Verification、Measurements、整体状态 |

规则：

- Facts 中禁止 `INFERRED`。
- 实际 Judgment、Root Cause 和 Prescription 使用 `INFERRED`，并必须有完整引用链。
- `UNKNOWN`、`NOT_RUN`、`INSUFFICIENT_DATA` 对应的测量值必须是 `null`，不能用
  `0`、`100` 或默认分代替。
- `VERIFIED` 不能仅由“材料中出现了某个词”触发。

## 唯一对外报告

最终用户只看到固定的一页报告：

```markdown
# 客户 GEO 快速诊断

## 一、客户定位
一句话定位：
核心业务：
主要客户：
主要应用场景：

## 二、当前 AI / GEO 状态
2—4 句话整体判断。

## 三、当前主要问题
最多 5 条。

## 四、下一步优化方向
P0：
P1：
P2：

## 五、诊断依据
最关键的 3—5 条公开事实或证据。
```

报告层只能执行：

- 字段映射
- 分组和排序已确定的数据
- 格式转换
- 展示裁剪
- 依据对象 ID 做溯源展示

报告层禁止：

- 重新计算评分
- 新增 Diagnostic Measurement
- 生成 Gap
- 生成 Judgment、Root Cause 或 Prescription
- 修改业务优先级
- 把推测改写为事实

最终报告禁止展示多套评分、多套 Gap、九大画像、关键词矩阵、内容矩阵、固定
30/60/90 天计划、复杂技术字段、Agent 运行过程或大量 JSON。内部 Facts、Evidence、
Measurements、Judgments、Root Causes、Prescriptions 默认不直接展示。

## 阶段 0 兼容状态

阶段 0 只冻结规范和合同，当前 `engine/pipeline.py` 尚未迁移。现有主链仍输出旧的
V2/V3 20 块结构，其中保留关键词、画像、内容建议、固定处方和报告层判断等历史能力。
这些能力当前不删除，但不再属于标准 GEO-BD 合同。

- 标准 Schema：`schemas/diagnostic.schema.json`
- Legacy Schema：`schemas/diagnostic-legacy.schema.json`
- 当前旧 Pipeline 回归测试：显式使用 Legacy Schema
- 新功能和新输出：只能面向标准 Schema

默认 Schema 校验命令面向标准合同：

```bash
python3 scripts/validate_diagnostic.py --input path/to/standard-diagnostic.json
```

阶段 0 如需检查当前旧 Pipeline 产物，必须显式指定兼容 Schema：

```bash
python3 scripts/validate_diagnostic.py \
  --input path/to/legacy-diagnostic.json \
  --schema schemas/diagnostic-legacy.schema.json
```

这项兼容不表示旧输出符合新合同。

## 当前入口

当前 Python 入口和旧功能在阶段 0 保持不变：

```bash
python3 scripts/run_diagnostic.py \
  --input tests/fixtures/sample_company.json \
  --summary \
  --offline
```

兼容入口 `run_diagnosis.py`、`generate_precheck.py` 和旧 renderer 暂不删除。它们的
输出不得作为标准合同示例。

## 测试

产品边界测试：

```bash
python3 -m pytest -q tests/test_product_boundary_contract.py
```

全量回归：

```bash
python3 -m pytest -q
```

边界测试通过仅表示阶段 0 的规范和 Schema 已冻结，不表示旧 Pipeline、Reporting 或
兼容模块已经完成阶段 1 迁移。
