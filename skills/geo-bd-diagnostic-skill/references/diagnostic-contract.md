# GEO-BD Standard Diagnostic Contract 1.0.0

机器可验证的唯一来源是
`geo-account-precheck/schemas/diagnostic.schema.json`。本文件解释其领域语义和引用规则。
除 `report_projection` 外，其他顶层对象均为内部推理和追溯数据，不直接展示给用户。

## 1. 完整顶层结构

```json
{
  "contract_version": "1.0.0",
  "meta": {
    "diagnostic_id": "string",
    "engine": "GEO-BD",
    "generated_at": "ISO-8601 string",
    "status": "STATUS",
    "input_snapshot_id": "string|null",
    "notes": []
  },
  "facts": [],
  "evidence_verification": [],
  "diagnostic_measurements": [],
  "judgments": [],
  "root_causes": [],
  "prescriptions": [],
  "report_projection": {
    "source_contract_version": "1.0.0",
    "status": "STATUS",
    "title": "客户 GEO 快速诊断",
    "customer_positioning": {},
    "ai_geo_status": {},
    "main_problems": [],
    "optimization_directions": {"P0": [], "P1": [], "P2": []},
    "diagnostic_basis": []
  }
}
```

顶层不允许额外字段。

## 2. Facts

```json
{
  "id": "FACT-company-name",
  "subject": "企业",
  "predicate": "名称",
  "value": "示例企业",
  "status": "PROVIDED",
  "source_ids": ["SOURCE-client-001"],
  "observed_at": null,
  "notes": null
}
```

- ID 前缀：`FACT-`。
- Facts 只允许 `VERIFIED`、`OBSERVED`、`PROVIDED`、`UNKNOWN`。
- `INFERRED` 永远不能进入 Facts。
- `UNKNOWN` 的 `value` 必须是 `null`。
- 非 UNKNOWN Fact 至少有一个来源 ID。

## 3. Evidence Verification

```json
{
  "id": "EVID-company-name",
  "fact_id": "FACT-company-name",
  "status": "VERIFIED",
  "method": "公开登记信息交叉核验",
  "source_ids": ["SOURCE-registry-001"],
  "conclusion": "名称一致",
  "conflicts": []
}
```

- ID 前缀：`EVID-`。
- 必须引用一个存在的 Fact ID。
- 只有完成明确核验方法并有来源时才能使用 `VERIFIED`。
- 未执行、数据不足或无法确认时分别使用 `NOT_RUN`、`INSUFFICIENT_DATA`、
  `UNKNOWN`。

## 4. Diagnostic Measurements

```json
{
  "id": "METRIC-ai-mention-rate",
  "name": "AI Mention Rate",
  "value": 40,
  "unit": "percent",
  "status": "OBSERVED",
  "fact_ids": ["FACT-ai-observation-001"],
  "evidence_ids": [],
  "basis": "5 条真实观察中有 2 条提及企业"
}
```

- ID 前缀：`METRIC-`。
- 至少引用一个存在的 Fact ID 或 Evidence ID。
- `UNKNOWN`、`NOT_RUN`、`INSUFFICIENT_DATA` 时 `value` 必须是 `null`。
- 不得用行业均值、默认值或模板值填补缺失测量。

## 5. Judgments

```json
{
  "id": "JUDGMENT-low-ai-visibility",
  "statement": "企业在已测试问题中的 AI 可见度较低",
  "status": "INFERRED",
  "source_fact_ids": [],
  "source_metric_ids": ["METRIC-ai-mention-rate"],
  "basis": "提及率低于本次诊断设定的可见度阈值",
  "confidence": 0.8
}
```

- ID 前缀：`JUDGMENT-`。
- 至少引用一个存在的 Fact ID 或 Metric ID。
- Judgment 是推导结果，只使用 `INFERRED`。
- 无依据时不创建 Judgment；不能用模板语句替代证据。

## 6. Root Causes

```json
{
  "id": "ROOT-missing-verifiable-presence",
  "statement": "可核验的企业公开信息不足",
  "status": "INFERRED",
  "judgment_ids": ["JUDGMENT-low-ai-visibility"],
  "basis": "多个诊断判断共同指向公开信源不足"
}
```

- ID 前缀：`ROOT-`。
- 至少引用一个存在的 Judgment ID。
- Root Cause 只使用 `INFERRED`。
- 业务建议、内容方案和行业常识不能当作根因。

## 7. Prescriptions

```json
{
  "id": "PRESCRIPTION-strengthen-verifiable-presence",
  "statement": "补齐可核验的企业公开信源",
  "status": "INFERRED",
  "root_cause_ids": ["ROOT-missing-verifiable-presence"],
  "priority": "P1",
  "expected_outcome": "关键企业事实能够被独立来源核验",
  "verification_method": "重新执行同口径 Evidence Verification",
  "handoff_to": "GEO"
}
```

- ID 前缀：`PRESCRIPTION-`。
- 至少引用一个存在的 Root Cause ID。
- Prescription 只描述要修复的能力、预期结果和验收方法。
- 优先级只允许 `P0`、`P1`、`P2`。
- 禁止在处方中生成关键词、画像、内容、发布计划、媒体计划或运营排期。

## 8. Report Projection

```json
{
  "source_contract_version": "1.0.0",
  "status": "INFERRED",
  "title": "客户 GEO 快速诊断",
  "customer_positioning": {
    "one_sentence": "示例企业是一家提供工业系统集成服务的企业",
    "core_business": ["工业系统集成"],
    "main_customers": ["工业企业"],
    "main_scenarios": ["工业项目采购"],
    "source_ids": ["FACT-company-business"]
  },
  "ai_geo_status": {
    "summary": "AI 已能识别企业基础业务，但权威证据和应用场景认知不足。",
    "source_ids": ["JUDGMENT-low-ai-visibility"]
  },
  "main_problems": [
    {
      "problem": "权威证据支撑不足",
      "source_ids": ["ROOT-missing-verifiable-presence"]
    }
  ],
  "optimization_directions": {
    "P0": [],
    "P1": [
      {
        "direction": "补齐可核验的企业公开信源",
        "prescription_ids": ["PRESCRIPTION-strengthen-verifiable-presence"]
      }
    ],
    "P2": []
  },
  "diagnostic_basis": [
    {"statement": "企业主营工业系统集成", "source_ids": ["FACT-company-business"]},
    {"statement": "AI 提及率来自真实观察", "source_ids": ["METRIC-ai-mention-rate"]},
    {"statement": "公开信源不足是当前根因", "source_ids": ["ROOT-missing-verifiable-presence"]}
  ]
}
```

Projection 是唯一用户可见结果，固定为：客户定位、AI/GEO 状态、最多 5 条主要问题、
P0/P1/P2 优化方向、3—5 条关键依据。所有内容必须引用既有对象；报告层不能重新计算。

最终报告控制在一页左右，不展示内部数组、完整引用链、多套 Score、Gap、Agent 过程、
技术 Schema 或大量 JSON。

## 9. 统一状态矩阵

| 状态 | 精确定义 | Facts | Evidence | Measurements | Judgments | Root Causes | Prescriptions |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `VERIFIED` | 已按明确方法由可追溯来源确认 | ✓ | ✓ | ✓ | — | — | — |
| `OBSERVED` | 直接观察结果，未必独立核验 | ✓ | — | ✓ | — | — | — |
| `PROVIDED` | 客户或上游提供，未独立核验 | ✓ | — | ✓ | — | — | — |
| `INFERRED` | 由引用对象推导 | — | — | ✓ | ✓ | ✓ | ✓ |
| `UNKNOWN` | 当前不知道 | ✓ | ✓ | ✓ | — | — | — |
| `NOT_RUN` | 检查未执行 | — | ✓ | ✓ | — | — | — |
| `INSUFFICIENT_DATA` | 已尝试但数据不足 | — | ✓ | ✓ | — | — | — |

Judgment、Root Cause、Prescription 没有足够数据时不创建占位结论；由 `meta.status`
或对应 Measurement 表达 `INSUFFICIENT_DATA`。

## 10. 禁止字段与内容

标准合同禁止：

- `generated_keywords`
- `generated_personas`
- `generated_content`
- `publishing_plan`
- `media_plan`
- `generated_market_queries`
- `target_market_queries`
- `plan_30_60_90`
- 任何同义的自动生成关键词、画像、内容、媒体或运营排期字段

Legacy V1 输出 Schema 仅作迁移兼容，不是标准合同来源。标准用户报告模板见
`report-template.md`。
