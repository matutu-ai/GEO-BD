# Diagnostic Skill V1 输出契约

`run_geo_bd_diagnostic.py --json` 输出 `diagnostic-output.schema.json` 定义的 JSON。它是面向 GEO Strategy 的稳定摘要层，底层完整事实仍保留在 `diagnostic.json` 和 `report.json`。

## 五类评分映射

| V1 类别 | 来源 | 说明 |
|---|---|---|
| Entity | `scores.entity_score` | 企业实体字段完整度 |
| AI Visibility | `scores.ai_cognition_score` | 真实 AI 观察中的提及、理解和认知 |
| Query Coverage | `scores.query_coverage_score` | 真实观察覆盖目标 Query 的程度 |
| Evidence | `scores.evidence_score` | Evidence 来源、日期、核验与冲突检查 |
| Authority | `eeat.authoritativeness` | 资质、专家、媒体、专利等权威基础 |

五类各占 20 分。V1 总分只有在五类都有可用数值时计算；单类分数可以先展示，不能把缺失类别当成 0。

## AI 认知字段

`brand_recognition` 对应真实观察的 Mention，`business_understanding` 和 `accuracy_score` 对应正确描述，`recommend_probability` 对应 Recommendation。没有 `observed/provided` 观察时全部为 `null`，状态为 `UNKNOWN`。

## 交接边界

V1 输出诊断状态、缺口和优化优先级；关键词扩展、内容写作、发布排期和生产执行属于后续 GEO Strategy / GEO Production，不在本 Skill 内实现。
