# GEO Diagnostic Engine 10 秒上手

下面的文件都是虚拟示例，只能用来练习和熟悉字段，不能当真实客户诊断结果使用。

## 1. 直接运行

在 `geo-account-precheck/` 目录执行：

```bash
python3 scripts/run_diagnostic.py \
  --input examples/01-quickstart.json \
  --output reports/quickstart.md \
  --json reports/quickstart.json \
  --needs-input reports/quickstart-needs.md \
  --offline
```

终端会直接显示一屏摘要，不需要先打开完整报告：

```text
GEO Score: 75 COMPUTED
Top P1: 提升信任基础与来源核验
Evidence: 52/100
Missing: founders、media、address、phone、social_accounts、reviews 等 7 项
AI Test: COMPUTED（1 条）
Next: 补充真实观察后，用同一批 Query 复测并 compare_reports
```

## 2. 只看摘要，不生成文件

```bash
python3 scripts/run_diagnostic.py \
  --input examples/01-quickstart.json \
  --summary \
  --offline
```

## 3. 校验结果

```bash
python3 scripts/validate_diagnostic.py --input reports/quickstart.json
```

## 4. 把示例换成真实客户

把 `company` 改成真实企业资料，把 `ai_observations` 换成真实 AI 回答，把
`evidence` 和 `competitors` 换成带来源的记录。缺少的部分保持为空，引擎会输出
`UNKNOWN / NOT_RUN / INSUFFICIENT_DATA`。

## 5. 第二轮复测

先跑完第一轮得到 `reports/quickstart.json`，再生成只保留静态企业资料的下一轮输入：

```bash
python3 scripts/prepare_round.py \
  --from reports/quickstart.json \
  --out inputs/round2.json
```

`prepare_round.py` 只复制公司资料和原始材料清单，会清空 AI 观察、竞品、Evidence 和指标，
避免把上一轮检测数字当成下一轮结果。
