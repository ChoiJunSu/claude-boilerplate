# Evals

`python evals/run.py`

- **strategy_cases.jsonl** — deterministic checks on the contrarian decision
  logic (`strategy.decide`). No API key needed. Gates the exit code.
- **crowd_cases.jsonl** — checks the Claude "dumb crowd" persona
  (`crowd.assess`) produces the expected `urge` for blow-off-top / capitulation
  / sideways scenarios. Needs `ANTHROPIC_API_KEY`; generative, so misses are
  reported as soft signal (don't gate the exit code).
