# GEO-BD

GEO-BD 是企业 GEO 诊断引擎，不是企业背调工具，也不是 GEO 执行系统。

## 唯一产品边界

标准主链固定为：

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

职责边界固定为：

```text
GEO-BD：事实 → 判断 → 根因 → 处方
GEO：关键词 → 画像 → 内容 → 发布 → 运营 → 复测执行
```

GEO-BD 不得自动生成关键词、画像、内容、发布计划、媒体投放计划、目标市场
Query 或固定 30/60/90 天运营计划。Reporting 只能投影已存在的诊断结果，不能
二次诊断、重新评分、生成 Gap 或产生新的业务判断。

## 唯一对外结果

输入只要求客户名称或客户基础资料。用户最终只看到一页《客户 GEO 快速诊断》：

```text
客户定位
→ 当前 AI / GEO 状态
→ 当前主要问题（最多 5 条）
→ 下一步优化方向（P0 / P1 / P2）
→ 诊断依据（最关键的 3—5 条）
```

客户定位必须回答“这家公司是谁、主要做什么、如何一句话定位”。优化方向只给能力
方向，不生成执行物。多套评分、多套 Gap、九大画像、关键词矩阵、内容矩阵、复杂技术
字段、Agent 过程和大量 JSON 信息都不得出现在最终用户报告中。

## 唯一标准诊断合同

标准合同是
[geo-account-precheck/schemas/diagnostic.schema.json](geo-account-precheck/schemas/diagnostic.schema.json)。
顶层严格分离：

- `facts`
- `evidence_verification`
- `diagnostic_measurements`
- `judgments`
- `root_causes`
- `prescriptions`
- `report_projection`（唯一对外一页结果）

强制引用链：

```text
Judgment ──→ Fact ID 或 Diagnostic Metric ID
Root Cause ──→ Judgment ID
Prescription ──→ Root Cause ID
```

允许的统一状态只有：`VERIFIED`、`OBSERVED`、`PROVIDED`、`INFERRED`、
`UNKNOWN`、`NOT_RUN`、`INSUFFICIENT_DATA`。未知或未执行的指标值必须是
`null`，不得自动变成 `0` 或 `100`。

## 当前迁移状态

阶段 0 只冻结边界、合同和测试，尚未改造旧 Pipeline。现有 Python 主链仍可能
输出旧 V2/V3 20 块结构并包含越界能力；该旧结构仅由
`geo-account-precheck/schemas/diagnostic-legacy.schema.json` 描述，不是标准合同。
旧模块本阶段不删除、不迁移，下一阶段才允许断开。

未跟踪的 `geo-account-precheck-rs/` 不属于本阶段范围，也不是标准实现来源。

## 阅读与验证

1. [LEARN.md](LEARN.md)：最短学习路径与模块责任。
2. [geo-account-precheck/AGENTS.md](geo-account-precheck/AGENTS.md)：修改约束。
3. [geo-account-precheck/SKILL.md](geo-account-precheck/SKILL.md)：Engine Skill。
4. [skills/geo-bd-diagnostic-skill/SKILL.md](skills/geo-bd-diagnostic-skill/SKILL.md)：诊断 Skill。

阶段 0 验证命令：

```bash
cd geo-account-precheck
python3 -m pytest -q tests/test_product_boundary_contract.py
python3 -m pytest -q
```

核心代码位于 `geo-account-precheck/`。不得提交客户资料、生成报告或本地构建产物。
