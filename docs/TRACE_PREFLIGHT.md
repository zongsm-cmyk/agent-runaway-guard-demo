# Agent Loop Trace Preflight — free offline scanner

**Purpose:** Find obvious repeat and alternating-tool patterns in a **sanitized, historical** AI-agent tool-call log before spending on a runtime protection layer.

**Price:** Free. **Install:** Python 3.10+ only; no pip packages and no network access. **Input:** normalized JSON Lines. **Output:** aggregate summary or redacted JSON; raw tool arguments are not printed.

This small public sample complements, but does not replace, the commercial Agent Runaway Guard Kit.

## Try the synthetic example

From this repository root:

```bash
python trace_preflight.py examples/agent_trace_sample.jsonl
python trace_preflight.py examples/agent_trace_sample.jsonl --json
python -m unittest discover -s tests -p 'test_trace_preflight.py' -v
```

The sample is entirely fictional. The scanner should flag **one alternating search/read pattern** and **one run of three identical fetch calls**, and report **$0.15 of user-supplied estimated trace cost**. This is a synthetic input total, **not an actual model bill or claimed savings**.

Exit codes: `0` clean, `2` suspicious repeat/cycle detected, `1` invalid input.

## Input contract: a small, normalized trace

Write one JSON object per line. Example:

```json
{"tool":"search","args":{"query":"fictional-example"},"estimated_cost_usd":"0.01"}
```

Required: `tool` is a nonempty string; `args` is a JSON object. Optional: `estimated_cost_usd` is a nonnegative decimal amount for that event, supplied by **you**. The scanner never queries provider billing. Cost defaults to zero if omitted. Event order is file order. Other keys are ignored.

For Claude Code, LangGraph, CrewAI or other runtimes, **first map the platform's events to this documented format**. There is no claim of native, plug-and-play parsing of vendor log formats.

**Before using any real trace:** remove API keys, tokens, passwords, usernames, customer payloads, URLs with embedded credentials, and private business information. Tool arguments are hashed in memory for comparison; the tool does **not** read them out in reports, but it still reads the input file. The file stays on your machine. Never upload a private agent trace to public GitHub.

## What this detects

- Consecutive calls of the same tool with identical canonical JSON arguments (default threshold: three).
- Alternating `A -> B -> A -> B` or longer two-step cycles with unchanged tool+argument fingerprints.
- Per-tool call counts and the sum of **provided** estimated cost fields.

Different key order in an `args` JSON object does not count as different arguments. Changes to the arguments DO change the fingerprint. This tool does not evaluate semantic equivalence, intent, success, budget efficacy or causation.

The scanner rejects non-JSONL input, missing required fields, negative/invalid costs, logs above 5 MiB, and traces beyond 10,000 events. Split large files. It is not a comprehensive secrets scanner.

## Five-minute incident triage

1. **Stop the active run with your platform's approved stop control** if it is still spending money.
2. **Check actual provider usage** to determine whether the suspected incident caused a charge. Do not infer actual bills from the synthetic sample.
3. Export only safe and redacted tool-event metadata and normalize it to the JSONL contract above.
4. Run this scanner; inspect exact line ranges and tool-call patterns it flags.
5. Add explicit per-run call/cost/time budgets, retry ceilings, stop conditions, and tests **before** running again. Re-run with synthetic inputs first.

## When is the paid kit relevant?

The [Agent Runaway Guard Kit — $24 on Gumroad](https://mhamedasskoure.gumroad.com/l/agent-runaway-guard-kit?utm_source=github&utm_medium=free_proof&utm_campaign=trace_preflight_20261108) includes actual **pre-dispatch** Python guards, canonical call fingerprints, 2–3 step cycle detection, retry budgets, token/cost/time ceilings, integer micro-dollar accounting, CI regression gates, a synthetic replay corpus and integration documentation.

**Difference:** This free scanner looks at a trace **after the fact**. The commercial kit's guard layer is designed to reject selected actions **before they run**, when integrated into your workflow and configured with appropriate budgets. Neither tool guarantees correctness or savings, and a false positive can represent a legitimate repeated task. Inspect the [live product description](https://mhamedasskoure.gumroad.com/l/agent-runaway-guard-kit) for current file list, license and checkout terms.

**Disclosure:** The author of this free scanner sells the optional paid kit. No purchase or email signup is required to use this sample. Neither project is affiliated with any model provider or agent framework.
