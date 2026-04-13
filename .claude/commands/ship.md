---
description: Commit, push, and merge to the deploy branch so the connected platform auto-deploys
argument-hint: [optional target override, e.g. "modal"]
---

$ARGUMENTS

Delegate to the `shipper` subagent. The default path is **Git-based deploy**: preflight → commit → push → merge to deploy branch → platform auto-builds. Only fall back to CLI deploy if the target (e.g. Modal) requires it or if the user specified one in `$ARGUMENTS`.

The shipper must:

1. Detect the deploy platform from repo signals (`vercel.json`, `fly.toml`, `railway.json`, `wrangler.toml`, `modal.*`). Ask the user if nothing matches.
2. Run preflight: clean tree check, stack-appropriate build/test smoke, secret scan of staged diff.
3. Commit + push to current branch.
4. If current branch isn't the deploy branch, confirm with the user before merging. Never force-push.
5. Print commit SHA and point at the platform dashboard. Remind the user to smoke-test the deployed URL once the build finishes.
