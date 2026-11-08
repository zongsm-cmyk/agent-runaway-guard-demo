# Agent Runaway Guard — Public Proof

[![proof-ci](https://github.com/zongsm-cmyk/agent-runaway-guard-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/zongsm-cmyk/agent-runaway-guard-demo/actions/workflows/ci.yml)

**External directory listing:** [Agent Runaway Guard Kit on AI Agents Info](https://www.aiagentsinfo.com/directory/agent-runaway-guard-kit) (community-submitted on 8 Nov 2026; **not** an independent review or customer endorsement). The free trace preflight below remains usable without a purchase.

Small, runnable proof for two failure modes that make autonomous AI agents expensive:

1. repeated identical tool calls;
2. projected LLM spend that crosses a run budget.

This repository is intentionally small. It proves the integration pattern without publishing the
commercial kit's cycle detector, retry-storm guard, regression CLI, synthetic replay corpus,
incident tooling, or full QA package.

## New: free offline trace preflight (post-run)

Have a suspicious agent execution log? Run the [free Agent Loop Trace Preflight](docs/TRACE_PREFLIGHT.md) against the included synthetic JSONL example or a **sanitized, normalized** event trace. It identifies repeated identical calls and simple A→B→A→B patterns **after a run**, without making API calls or printing tool arguments.

```bash
python trace_preflight.py examples/agent_trace_sample.jsonl --json
```

This is not a production guard or native Claude Code log importer. For **pre-dispatch** runtime protection, see the separate [$24 commercial kit](https://mhamedasskoure.gumroad.com/l/agent-runaway-guard-kit?utm_source=github&utm_medium=free_trace&utm_campaign=agent_trace_launch_20261108).

## Try the free proof, then choose the full kit

This public demo is intentionally free and runnable in Python. It reproduces a repeated-tool-call guard so you can inspect the behavior **before spending anything**.

If that is the failure mode you need to control, the optional [Agent Runaway Guard Kit ($24)](https://mhamedasskoure.gumroad.com/l/agent-runaway-guard-kit?utm_source=github&utm_medium=free_demo&utm_campaign=agent_guard_first_sale_20261108) adds the documented local loop, retry-storm and budget-boundary checks plus regression resources. The demo does not establish any production cost savings or guarantee it can prevent every kind of runaway execution.

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