---
description: Implement the approved plan using the builder agent
argument-hint: [optional focus, e.g. "just the agent loop"]
---

$ARGUMENTS

Delegate to the `builder` subagent. It should:

1. Read `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `CLAUDE.md`.
2. Implement the must-have features in PRD order, committing after each.
3. Apply prompt caching, use latest model IDs, and follow the user-level `claude-api` skill when touching Anthropic SDK code.
4. Run a smoke check (dev server, tests, or script import) after each commit.
5. Return a ≤5-bullet summary of what shipped and suggest `/eval` or `/ship` as the next step.

If `$ARGUMENTS` is non-empty, narrow the builder's scope to just that.
