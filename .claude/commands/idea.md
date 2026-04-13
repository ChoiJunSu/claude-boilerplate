---
description: Turn a rough idea into docs/PRD.md and docs/ARCHITECTURE.md
argument-hint: <one-line description of the idea>
---

The user has a new idea: **$ARGUMENTS**

Delegate to the `planner` subagent. Pass the idea above and instruct it to:

1. Read `docs/PRD.template.md` and `docs/ARCHITECTURE.template.md`.
2. Ask at most one round of clarifying questions (max 3 questions) if the idea is ambiguous.
3. Write `docs/PRD.md` and `docs/ARCHITECTURE.md` following the templates.
4. Return a two-line summary with links to both files.

Do not implement anything yourself in this turn. If `docs/PRD.md` already exists, ask the user whether to overwrite it before delegating.
