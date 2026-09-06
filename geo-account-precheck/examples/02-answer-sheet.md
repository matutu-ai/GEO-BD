# GEO 诊断报告速查表

## 先看哪一屏

运行命令后终端摘要已经给出最重要的 5 个信号：

| 信号 | 含义 |
|---|---|
| `GEO Score: 75 COMPUTED` | 九维加权总分；缺数据时不是 0，而是 `INSUFFICIENT_DATA` |
| `Top P1: 提升信任基础与来源核验` | 第一件应该做的事 |
| `Evidence: 52/100` | 核验材料是否够扎实 |
| `Missing: founders、media...` | 还缺哪些企业字段 |
| `AI Test: COMPUTED（1 条）` | Mention/Recommendation/Citation 是否有真实样本 |

## JSON 顶层对应关系

| 你关心的业务问题 | 先看 JSON 块 |
|---|---|
| AI 知不知道公司 | `entity`、`ai_cognition` |
| AI 推荐谁、为什么不推荐我 | `query_matrix`、`competitors` |
| 资料够不够、可信不可信 | `evidence_graph`、`data_quality` |
| 哪些搜索场景缺席 | `scenarios`、`keywords` |
| 是否被引用 | `citations`、`ai_tests` |
| 最大差距 | `gaps` |
| 先做什么 | `opportunities`、`recommendations` |
| 复测后涨没涨 | `validation`、`scores` |

## 最常用的输入字段

| JSON 字段 | 填什么 | 反例 |
|---|---|---|
| `company.name` | 公司全称 | 只填客户昵称 |
| `company.business` | 主营业务，一句讲清 | 写营销口号 |
| `company.cases` | 真实项目案例 | 把案例参数编出来 |
| `materials` | 已经收集到的官网、证书、媒体报道 | 写成待办清单 |
| `ai_observations` | 真实 AI 问答记录，`observation_mode=observed` | 自己预测 AI 会怎么说 |
| `competitors` | 已确认竞品及来源 | 让系统替你猜竞品 |
| `evidence` | 声明、来源、日期、来源类型 | 没有来源却写 `FACT` |

## 状态速记

| 状态 | 意思 |
|---|---|
| `FACT` | 有明确来源；用户资料记为 `user_provided`，`verified=false` |
| `INFERENCE` | 引擎基于输入推导，不作为外部事实 |
| `UNKNOWN` | 没有可靠数据 |
| `NOT_RUN` | 没有真实 AI 测试，不能算 Mention/Citation 数字 |
| `INSUFFICIENT_DATA` | 可评分维度太少，整体分数不成立 |

## 一个工作循环

```text
run_diagnostic -> 看一屏摘要 -> 打开 needs-input 清单
-> 补真实资料 -> prepare_round -> run_diagnostic
-> 用同一批 Query 做真实 AI Test -> compare_reports
```
