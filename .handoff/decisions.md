# Confirmed Decisions

- GEO-BD owns facts, judgments, root causes, and prescriptions.
- GEO owns keywords, personas, content, publishing, operations, and retest execution.
- The canonical contract is `geo-account-precheck/schemas/diagnostic.schema.json`.
- The unchanged old Pipeline contract is retained as `diagnostic-legacy.schema.json` during migration.
- Reporting is projection-only and cannot compute diagnostic conclusions.
- The only standard statuses are VERIFIED, OBSERVED, PROVIDED, INFERRED, UNKNOWN, NOT_RUN, and INSUFFICIENT_DATA.
- The only user-facing result is a one-page `客户 GEO 快速诊断`.
- The user-facing result contains customer positioning, AI/GEO status, at most five problems, P0/P1/P2 directions, and three to five key facts or evidence items.
- Facts, Evidence, Measurements, Judgments, Root Causes, and Prescriptions remain internal and traceable.
- Scores, Gap systems, personas, keyword/content matrices, 30/60/90 plans, Agent traces, Schema details, and full JSON are hidden from the final user report.
