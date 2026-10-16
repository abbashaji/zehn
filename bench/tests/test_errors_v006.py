"""v006: API-failure records are redone by --resume and left out of reports; rounds may carry diag messages."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

import _common as c
from benchlib import loop, schema, store
import report
from test_core_loop import run

API_ERR = "ModelError: giving up after 6 attempts (HTTP 503: {\n \"error\": {}"


def rec(task, lang, repeat, error=None, passed=True):
    return {"schema": 1, "run_id": "r", "set": "dev", "task_id": task, "category": "pure", "kind": "write",
            "lang": lang, "variant": "default", "model": "m", "repeat": repeat, "temperature": 1.0,
            "rounds": [] if error else [{"i": 1, "tool_ok": True, "diag_codes": [], "unknown_names": 0,
                                         "in_tokens": 1, "out_tokens": 1}],
            "accepted_round": None if error else 1, "first_try_pass": passed and not error,
            "final_pass": passed and not error, "final_tests": {"passed": 1 if passed and not error else 0, "total": 1},
            "total_in_tokens": 1, "total_out_tokens": 1, "wall_ms": 1, "error": error}


def write(path, recs):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


class ErrorHandlingTests(unittest.TestCase):
    def test_retryable_only_for_api_failures(self):
        self.assertTrue(loop.is_retryable_error({"error": API_ERR}))
        self.assertTrue(loop.is_retryable_error({"error": "ModelError: giving up after 6 attempts (HTTP 429: x"}))
        self.assertFalse(loop.is_retryable_error({"error": "ModelError: giving up after 6 attempts (HTTP 400: x"}))
        self.assertFalse(loop.is_retryable_error({"error": "tool_check crashed: KeyError: 'x'"}))
        self.assertFalse(loop.is_retryable_error({"error": None}))

    def test_prune_moves_only_api_failures(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "records.jsonl")
            keep = [rec("a", "zehn", 1), rec("b", "zehn", 1, error="tool_check crashed: X")]
            write(p, [keep[0], rec("c", "zehn", 1, error=API_ERR), keep[1]])
            self.assertEqual(store.prune_api_errors(p), 1)
            self.assertEqual([json.loads(x)["task_id"] for x in open(p)], ["a", "b"])
            moved = [json.loads(x) for x in open(os.path.join(d, "records.errors.jsonl"))]
            self.assertEqual([m["task_id"] for m in moved], ["c"])
            self.assertEqual(store.prune_api_errors(p), 0)

    def test_resume_prunes(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "r1"))
            write(os.path.join(d, "r1", "records.jsonl"), [rec("a", "zehn", 1, error=API_ERR)])
            rs = store.RunStore(d, "r1", resume=True)
            self.assertEqual(rs.pruned, 1)
            self.assertEqual(open(rs.records_path).read(), "")

    def test_report_leaves_errored_runs_out(self):
        with tempfile.TemporaryDirectory() as d:
            recs = [rec("a", "zehn", 1), rec("b", "zehn", 1, error=API_ERR), rec("a", "python_plain", 1)]
            write(os.path.join(d, "records.jsonl"), recs)
            text = report.build_report([d])
        self.assertIn("## Runs left out (ended on an error)", text)
        row = [x for x in text.split("\n") if x.startswith("| zehn | 1 | 1 |")]
        self.assertTrue(row, text)
        res = [x for x in text.split("\n") if x.startswith("| zehn | default |")][0]
        self.assertIn("| 1 | 1 |", res)          # 1 task, 1 run: the errored run is not counted
        self.assertIn("1.000", res)

    def test_report_without_errors_has_no_section(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "records.jsonl"), [rec("a", "zehn", 1)])
            self.assertNotIn("Runs left out", report.build_report([d]))


    def test_exclude_errors_flag_changes_n_not_other_metrics(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as clean:
            ok = [rec("a", "zehn", 1), rec("b", "zehn", 1, passed=False), rec("a", "python_plain", 1)]
            write(os.path.join(d, "records.jsonl"), ok + [rec("c", "zehn", 1, error=API_ERR)])
            write(os.path.join(clean, "records.jsonl"), ok)
            with_err = report.build_report([d], exclude_errors=True)
            without = report.build_report([clean], exclude_errors=True)
        self.assertIn("| zehn | 2 | 1 | ModelError: giving up after 6 attempts (HTTP 503: { \"error\": {} (x1) |", with_err)
        self.assertIn("| zehn | 2 | 0 | - |", without)          # zero row printed when nothing was dropped
        self.assertIn("| python_plain | 1 | 0 | - |", without)
        pick = lambda text, lang: [x for x in text.split("\n") if x.startswith("| %s | default |" % lang)]
        self.assertEqual(pick(with_err, "zehn"), pick(without, "zehn"))               # same n and metrics
        self.assertEqual(pick(with_err, "python_plain"), pick(without, "python_plain"))
        self.assertIn("| 2 | 2 |", pick(with_err, "zehn")[0])                           # 2 tasks, 2 runs: errored one not counted


class DiagMessageTests(unittest.TestCase):
    def test_failed_round_records_messages_and_validates(self):
        from benchlib.models import get_model
        r, _ = run("zehn", get_model("stub:broken_then_fixed"))
        self.assertEqual(schema.validate_record(r), [])
        d = r["rounds"][0]["diags"]
        self.assertTrue(d and all(set(x) == {"code", "line", "message"} and len(x["message"]) <= 300 for x in d))
        self.assertEqual([x["code"] for x in d], r["rounds"][0]["diag_codes"][:len(d)])

    def test_schema_accepts_old_rounds_and_rejects_bad_diags(self):
        r = rec("a", "zehn", 1)
        self.assertEqual(schema.validate_record(r), [])
        r["rounds"][0]["diags"] = [{"code": "E1", "line": None, "message": "m"}]
        self.assertEqual(schema.validate_record(r), [])
        r["rounds"][0]["diags"] = [{"code": "E1"}]
        self.assertTrue(schema.validate_record(r))
        r["rounds"][0]["diags"] = "x"
        self.assertTrue(schema.validate_record(r))


if __name__ == "__main__":
    unittest.main()
