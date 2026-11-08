"""Offline, deterministic regression checks for free trace-preflight sample."""
import contextlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from trace_preflight import TraceError, analyze, fingerprint, main, read_trace


class TracePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "trace.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, events):
        self.path.write_text("\n".join(json.dumps(x) for x in events) + "\n", encoding="utf-8")
        return read_trace(self.path)

    def tool(self, name="search", args=None, cost="0.01"):
        return {"tool": name, "args": {"query": "sample"} if args is None else args,
                "estimated_cost_usd": cost}

    def test_empty_trace_is_not_flagged(self):
        self.path.write_text("", encoding="utf-8")
        report = analyze(read_trace(self.path))
        self.assertEqual(report["event_count"], 0)
        self.assertFalse(report["flagged"])

    def test_identical_three_calls_flagged(self):
        events = self.put([self.tool()] * 3)
        r = analyze(events)
        self.assertTrue(r["flagged"])
        self.assertEqual(r["identical_call_runs"][0]["calls"], 3)
        self.assertEqual(r["identical_call_runs"][0]["from_line"], 1)
        self.assertEqual(r["identical_call_runs"][0]["to_line"], 3)

    def test_canonical_argument_order(self):
        self.assertEqual(fingerprint("search", {"a": 1, "b": 2}),
                         fingerprint(" search ", {"b": 2, "a": 1}))

    def test_different_arguments_are_not_identical(self):
        events = self.put([self.tool(args={"q": "a"}),
                           self.tool(args={"q": "b"}),
                           self.tool(args={"q": "c"})])
        self.assertFalse(analyze(events)["flagged"])

    def test_two_step_cycle_detected_once(self):
        a, b = self.tool("search"), self.tool("read")
        report = analyze(self.put([a, b, a, b, a, b]))
        self.assertEqual(len(report["two_step_cycles"]), 1)
        self.assertEqual(report["two_step_cycles"][0]["calls"], 6)
        self.assertEqual(report["two_step_cycles"][0]["tools"], ["search", "read"])

    def test_constant_calls_not_mislabelled_as_two_step_cycle(self):
        report = analyze(self.put([self.tool()] * 4))
        self.assertEqual(report["two_step_cycles"], [])
        self.assertEqual(len(report["identical_call_runs"]), 1)

    def test_subthreshold_repeat_is_not_flagged(self):
        self.assertFalse(analyze(self.put([self.tool(), self.tool()]))["flagged"])

    def test_threshold_can_be_selected(self):
        self.assertTrue(analyze(self.put([self.tool(), self.tool()]), 2)["flagged"])

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(TraceError):
            analyze([], 1)

    def test_decimal_cost_uses_exact_sum(self):
        report = analyze(self.put([self.tool(cost="0.10"), self.tool("read", cost="0.20")]))
        self.assertEqual(report["estimated_cost_usd"], "0.30")

    def test_invalid_json_is_rejected(self):
        self.path.write_text("{invalid}\n", encoding="utf-8")
        with self.assertRaises(TraceError):
            read_trace(self.path)

    def test_non_object_event_rejected(self):
        self.path.write_text("[1,2]\n", encoding="utf-8")
        with self.assertRaisesRegex(TraceError, "expected a JSON object"):
            read_trace(self.path)

    def test_tool_and_args_required(self):
        self.path.write_text('{"tool":"test"}\n', encoding="utf-8")
        with self.assertRaisesRegex(TraceError, "args"):
            read_trace(self.path)

    def test_nonfinite_and_negative_costs_rejected(self):
        for cost in ["NaN", "-0.1", "Infinity"]:
            with self.subTest(cost=cost):
                self.path.write_text(json.dumps(self.tool(cost=cost)) + "\n", encoding="utf-8")
                with self.assertRaises(TraceError):
                    read_trace(self.path)

    def test_report_never_exposes_argument_values(self):
        secret = "DO_NOT_PRINT_FAKE_SECRET_TOKEN"
        report = analyze(self.put([self.tool(args={"token": secret})] * 3))
        self.assertNotIn(secret, json.dumps(report))
        self.assertNotIn("token", json.dumps(report))

    def test_bom_utf8_is_supported(self):
        self.path.write_text(json.dumps(self.tool()) + "\n", encoding="utf-8-sig")
        self.assertEqual(len(read_trace(self.path)), 1)

    def test_json_cli_exit_and_no_raw_args(self):
        self.put([self.tool(args={"token": "PRIVATE_VALUE"})] * 3)
        out = StringIO()
        with contextlib.redirect_stdout(out):
            code = main([str(self.path), "--json"])
        self.assertEqual(code, 2)
        self.assertTrue(json.loads(out.getvalue())["flagged"])
        self.assertNotIn("PRIVATE_VALUE", out.getvalue())

    def test_clean_cli_exit(self):
        self.put([self.tool(), self.tool("other")])
        with contextlib.redirect_stdout(StringIO()):
            code = main([str(self.path)])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
