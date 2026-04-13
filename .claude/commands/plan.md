---
description: Turn the current PRD + architecture doc into a file-by-file implementation plan
---

Read `docs/PRD.md` and `docs/ARCHITECTURE.md`. If either is missing, tell the user to run `/idea` first and stop.

Then enter plan mode and produce a concrete implementation plan:

- List each file to create or edit, in the order a builder should tackle them.
- For each file, one sentence on what goes in it.
- Call out any existing utilities in the repo that should be reused.
- Highlight the prompt-caching strategy and which model each call uses.
- End with a one-line verification plan (how we'll know v0.1 works).

Keep the plan tight — one screen. No phase-2 speculation. When done, call `ExitPlanMode` so the user can approve and move on to `/build`.
