# Agent Runaway Guard — Public Proof

[![proof-ci](https://github.com/zongsm-cmyk/agent-runaway-guard-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/zongsm-cmyk/agent-runaway-guard-demo/actions/workflows/ci.yml)

Small, runnable proof for two failure modes that make autonomous AI agents expensive:

1. repeated identical tool calls;
2. projected LLM spend that crosses a run budget.

This repository is intentionally small. It proves the integration pattern without publishing the
commercial kit's cycle detector, retry-storm guard, regression CLI, synthetic replay corpus,
incident tooling, or full QA package.

## Run it

```bash
python demo.py
```

Expected behavior: the third identical tool call is blocked before execution.

## Test it

```bash
python -m pip install pytest
python -m pytest -q
```
## Why this matters

A provider-level spend limit is useful, but it cannot tell you that one workflow is stuck repeating
the same action. A max-iterations setting is also blunt: it can waste budget inside a short loop.

The full commercial kit combines:

- canonical tool-call fingerprints;
- identical and 2–3 step cyclic-loop detection;
- retry-storm budgets;
- pre-dispatch call/token/cost/time limits;
- integer micro-dollar accounting;
- cost/token/LLM-call/tool-call CI regression gates;
- a 14-case synthetic failure-trace replay corpus;
- integration and incident documentation.

## Full kit

Agent Runaway Guard Kit v1.0.0:
https://mhamedasskoure.gumroad.com/l/agent-runaway-guard-kit?utm_source=github&utm_medium=organic&utm_campaign=winner_validation_20261025&utm_content=agent_runaway_demo_readme

Launch price: $24.