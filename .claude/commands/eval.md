---
description: Run the prompt eval set and write a report
---

Delegate to the `evaluator` subagent. It should:

1. Look for `evals/`. If empty, generate 5-8 starter cases from `docs/PRD.md` and save them.
2. Run each case through the app's entry point.
3. Capture pass/fail, latency, and token usage per case.
4. Write `docs/EVAL_REPORT.md` with a results table and a diff against the previous report if one exists.
5. Print the top-line (X/Y passed, total tokens) and flag any >2x token regressions.

Do not patch the app based on results — report only.
