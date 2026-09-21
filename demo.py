import hashlib
import json
from dataclasses import dataclass


def fingerprint(tool: str, args: object) -> str:
    payload = json.dumps(args, sort_keys=True, separators=(",", ":"), default=str)
    raw = f"{tool.strip()}|{payload}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass
class DemoGuard:
    max_identical_calls: int = 3
    max_cost_usd: float = 1.0

    def __post_init__(self) -> None:
        self._last: str | None = None
        self._repeats = 0
        self._cost = 0.0

    def before_tool(self, tool: str, args: object) -> None:
        current = fingerprint(tool, args)
        self._repeats = self._repeats + 1 if current == self._last else 1
        self._last = current
        if self._repeats >= self.max_identical_calls:
            raise RuntimeError("IDENTICAL_TOOL_LOOP")

    def before_llm(self, estimated_cost_usd: float) -> None:
        if self._cost + max(0.0, estimated_cost_usd) > self.max_cost_usd:
            raise RuntimeError("COST_BUDGET_EXCEEDED")

    def settle_llm(self, actual_cost_usd: float) -> None:
        self._cost += max(0.0, actual_cost_usd)


if __name__ == "__main__":
    guard = DemoGuard(max_identical_calls=3, max_cost_usd=0.50)
    for n in range(1, 5):
        try:
            guard.before_tool("search", {"q": "pricing"})
            print(f"tool call {n}: allowed")
        except RuntimeError as exc:
            print(f"tool call {n}: blocked -> {exc}")
            break