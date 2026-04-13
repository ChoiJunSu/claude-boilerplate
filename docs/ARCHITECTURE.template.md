# Architecture — {product name}

> Filled in by the `planner` agent via `/idea`. Focus on the Claude-specific pieces: model choice, prompts, tools, loop shape.

## Stack
- Runtime: (Node/TS? Python? Edge?)
- Entry point: (CLI? Next.js route? FastAPI?)
- Deploy target: (Vercel / Modal / Fly / local)

## Model Plan
Which model for which call, and why.

| Call | Model | Reason |
|---|---|---|
| Main agent loop | `claude-sonnet-4-6` | default |
| … | … | … |

## Agent Loop
Describe the loop in plain English. Example:

> User message → Sonnet 4.6 with tools `[search, fetch, answer]` → if `tool_use`, run tool, append `tool_result`, loop → if `end_turn` on `answer`, return to user.

## Tools
One table row per tool. Keep signatures minimal.

| Name | Input schema | Side effect | Notes |
|---|---|---|---|
| `search` | `{query: string}` | none | wraps Tavily |
| … | … | … | … |

## Prompts
- **System prompt**: where it lives, roughly what it says, what's cached.
- **Cache layout**: which blocks carry `cache_control`. (System? Tools? Few-shot?)

## Data
What's persisted, where, and why. If nothing is persisted, say so.

## Risks
Two or three things most likely to break. How we'd notice.
