---
description: Deploy the prototype to Vercel, Modal, or Fly
argument-hint: <vercel|modal|fly>
---

Target: **$ARGUMENTS**

Delegate to the `shipper` subagent. If `$ARGUMENTS` is empty, the shipper should ask which target to deploy to before doing anything.

The shipper must:

1. Run preflight: clean tree check, build/test, secret scan, env var check on the target platform.
2. Deploy with the correct command for the target.
3. Stream output; on failure, print the last ~30 lines and suggest a fix.
4. Print the deployed URL and remind the user to smoke-test it.

Never bypass preflight. Never force-push or force-deploy.
