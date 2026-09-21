import pytest

from demo import DemoGuard, fingerprint


def test_argument_order_has_same_fingerprint():
    assert fingerprint("search", {"a": 1, "b": 2}) == fingerprint("search", {"b": 2, "a": 1})


def test_third_identical_call_is_blocked():
    guard = DemoGuard(max_identical_calls=3)
    guard.before_tool("search", {"q": "pricing"})
    guard.before_tool("search", {"q": "pricing"})
    with pytest.raises(RuntimeError, match="IDENTICAL_TOOL_LOOP"):
        guard.before_tool("search", {"q": "pricing"})


def test_projected_cost_is_blocked_before_dispatch():
    guard = DemoGuard(max_cost_usd=0.50)
    guard.settle_llm(0.40)
    with pytest.raises(RuntimeError, match="COST_BUDGET_EXCEEDED"):
        guard.before_llm(0.15)