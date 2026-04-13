# claude-boilerplate

Personal prototyping template for shipping Claude API / Agent SDK apps from the **mobile Claude app** on Claude Code on the web.

Mobile idea → new repo from this template → `/idea` → `/plan` → `/build` → `/eval` → `/ship` → deployed. All in the cloud sandbox, all as commits.

## One-time setup

1. **Make this repo a GitHub template** — Settings → "Template repository" ✓
2. **Add repo-level secrets** (Settings → Secrets and variables → Actions, and the same under Codespaces/Claude Code on the web env):
   - `ANTHROPIC_API_KEY` (required)
   - Any deployment platform tokens you'll need (`VERCEL_TOKEN`, etc.)
3. **Connect your deploy platform to GitHub** (Vercel, Railway, Fly, Cloudflare, Render — whichever ships on push). This lets `/ship` deploy just by merging to `main`.

## Starting a new idea from your phone

1. In GitHub, "Use this template" → create a new repo (e.g. `recipe-ranker`).
2. Open the Claude mobile app → start a Claude Code session on the new repo.
3. Wait for the SessionStart hook to finish installing deps (see `.claude/hooks/session-start.sh`).
4. Run `/idea <one-line description>`. The planner writes `docs/PRD.md` + `docs/ARCHITECTURE.md`.
5. Run `/plan` → `/build` → `/eval` → `/ship`. Each step is a subagent tuned for that phase.

The full workflow and coding principles live in [`CLAUDE.md`](./CLAUDE.md).

## What's in the box

```
.claude/
├── settings.json           permissions, default model, SessionStart hook
├── hooks/
│   └── session-start.sh    stack-agnostic dep bootstrap for the web sandbox
├── agents/
│   ├── planner.md          idea → PRD + architecture (Opus 4.6)
│   ├── builder.md          PRD → code (Sonnet 4.6)
│   ├── evaluator.md        run evals/ → report
│   └── shipper.md          commit → push → merge → platform auto-deploy
└── commands/
    ├── idea.md  plan.md  build.md  eval.md  ship.md
.mcp.json                   context7 + fetch MCP servers
docs/
├── PRD.template.md         filled by planner
└── ARCHITECTURE.template.md
```

## Notes

- **Mobile-first.** Everything must be committed to the repo — the web sandbox does not read `~/.claude/`.
- **Secrets never live in files.** Put them in GitHub env vars. `.env` is gitignored; `.env.example` is for local-only runs.
- **Latest Claude models only.** `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`. Hardcoded, no fallbacks.
- **Prompt caching is mandatory** whenever `anthropic` / `@anthropic-ai/sdk` is imported. The user-level `claude-api` skill enforces this.
