#!/usr/bin/env python3
"""Free post-run agent tool-loop scan. Standard library only; offline by design.

Input: one JSON object per line: {"tool": "search", "args": {"q": "example"},
                                "estimated_cost_usd": "0.01"}.
This inspects sanitized *historical* events. It does not prevent tool execution.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

MAX_BYTES = 5 * 1024 * 1024
MAX_EVENTS = 10000
MAX_LINE = 100000


class TraceError(ValueError):
    """Invalid or unsafe-to-interpret trace input."""


def fingerprint(tool: str, args: dict[str, Any]) -> str:
    """Stable digest of canonical JSON; never display raw arguments."""
    packed = json.dumps(
        {"tool": tool.strip(), "args": args},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(packed).hexdigest()


def read_trace(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise TraceError("file not found")
    if path.stat().st_size > MAX_BYTES:
        raise TraceError("trace exceeds 5 MiB; split it before scanning")
    events: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8-sig") as source:
            for lineno, line in enumerate(source, 1):
                if not line.strip():
                    continue
                if len(line) > MAX_LINE:
                    raise TraceError(f"line {lineno}: line exceeds 100,000 characters")
                if len(events) >= MAX_EVENTS:
                    raise TraceError("more than 10,000 events; split your trace")
                try:
                    event = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                except (ValueError, json.JSONDecodeError) as exc:
                    raise TraceError(f"line {lineno}: invalid JSON ({exc})") from exc
                if not isinstance(event, dict):
                    raise TraceError(f"line {lineno}: expected a JSON object")
                tool, args = event.get("tool"), event.get("args")
                if not isinstance(tool, str) or not tool.strip():
                    raise TraceError(f"line {lineno}: non-empty string tool required")
                if not isinstance(args, dict):
                    raise TraceError(f"line {lineno}: args must be a JSON object")
                cost = event.get("estimated_cost_usd", "0")
                if isinstance(cost, bool) or not isinstance(cost, (str, int, float, Decimal)):
                    raise TraceError(f"line {lineno}: invalid estimated_cost_usd")
                try:
                    amount = Decimal(str(cost))
                except InvalidOperation as exc:
                    raise TraceError(f"line {lineno}: invalid estimated_cost_usd") from exc
                if not amount.is_finite() or amount < 0:
                    raise TraceError(f"line {lineno}: cost must be finite and nonnegative")
                try:
                    digest = fingerprint(tool, args)
                except (TypeError, ValueError) as exc:
                    raise TraceError(f"line {lineno}: invalid args structure") from exc
                events.append({"line": lineno, "tool": tool.strip(), "fingerprint": digest, "cost": amount})
    except UnicodeError as exc:
        raise TraceError("trace is not valid UTF-8") from exc
    return events


def analyze(events: list[dict[str, Any]], repeat_threshold: int = 3) -> dict[str, Any]:
    if repeat_threshold < 2:
        raise TraceError("repeat threshold must be at least 2")
    keys = [e["fingerprint"] for e in events]
    repeats: list[dict[str, Any]] = []
    cycles: list[dict[str, Any]] = []
    start = 0
    while start < len(keys):
        end = start + 1
        while end < len(keys) and keys[end] == keys[start]:
            end += 1
        if end - start >= repeat_threshold:
            repeats.append({
                "tool": events[start]["tool"], "from_line": events[start]["line"],
                "to_line": events[end - 1]["line"], "calls": end - start,
            })
        start = end

    start = 0
    while start + 3 < len(keys):
        if (keys[start] != keys[start + 1]
                and keys[start] == keys[start + 2]
                and keys[start + 1] == keys[start + 3]):
            end = start + 4
            while end < len(keys) and keys[end] == keys[end - 2]:
                end += 1
            cycles.append({
                "from_line": events[start]["line"],
                "to_line": events[end - 1]["line"],
                "calls": end - start,
                "tools": [events[start]["tool"], events[start + 1]["tool"]],
            })
            start = end
        else:
            start += 1

    counts = Counter(e["tool"] for e in events)
    total = sum((e["cost"] for e in events), Decimal("0"))
    return {
        "schema": "agent-loop-preflight/v1",
        "mode": "post-run-only",
        "event_count": len(events),
        "tool_counts": dict(sorted(counts.items())),
        "estimated_cost_usd": str(total),
        "repeat_threshold": repeat_threshold,
        "identical_call_runs": repeats,
        "two_step_cycles": cycles,
        "flagged": bool(repeats or cycles),
        "limitations": "Historical normalized trace only; not a live guard, billing meter or proof of wasted calls.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline post-run scan of sanitized JSONL agent tool calls")
    parser.add_argument("trace", type=Path, help="UTF-8 JSONL file with tool and args fields")
    parser.add_argument("--repeat-threshold", type=int, default=3, metavar="N")
    parser.add_argument("--json", action="store_true", help="emit redacted machine-readable JSON")
    opts = parser.parse_args(argv)
    try:
        report = analyze(read_trace(opts.trace), opts.repeat_threshold)
    except (TraceError, OSError) as exc:
        print(f"Trace rejected: {exc}", file=sys.stderr)
        return 1
    if opts.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Events: {report['event_count']} | Estimated trace cost: ${report['estimated_cost_usd']}")
        print(f"Identical-call runs: {len(report['identical_call_runs'])} | 2-step cycles: {len(report['two_step_cycles'])}")
        for item in report["identical_call_runs"]:
            print(f"  REPEAT {item['tool']}: {item['calls']} calls (lines {item['from_line']}-{item['to_line']})")
        for item in report["two_step_cycles"]:
            print(f"  CYCLE {item['tools'][0]} -> {item['tools'][1]}: {item['calls']} calls (lines {item['from_line']}-{item['to_line']})")
        print("Post-run signal only; no production protection or verified cost savings.")
    return 2 if report["flagged"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
