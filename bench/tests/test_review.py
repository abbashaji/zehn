"""Bet 1 review experiment: mutation operators, item invariants, reply parsing, run + report with a fake model."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import review as review_cli  # noqa: E402
from benchlib import mutate, review, schema  # noqa: E402

ZEHN = '''fn f(a: Int, b: Int) -> Int
  intent "x + 1 stays in the intent"
  requires a > 0
  example f(1, 2) == 3
do
  let s = "a + b"
  return a + b + 1
end fn
'''
PY = '''def f(a: int, b: int) -> int:
    """a + b"""
    # a + b
    return a + b + 1
'''


class MutateTests(unittest.TestCase):
    def test_zehn_touches_only_the_body_and_never_strings(self):
        ms = mutate.mutants(ZEHN, "zehn")
        self.assertTrue(ms)
        for m in ms:
            self.assertGreaterEqual(m["line"], 7)                      # after `do`
            self.assertIn('let s = "a + b"', m["source"])
            self.assertIn('intent "x + 1 stays in the intent"', m["source"])
            self.assertIn("example f(1, 2) == 3", m["source"])
            self.assertEqual(len(m["source"].split("\n")), len(ZEHN.split("\n")))
        ops = {m["op"] for m in ms}
        self.assertIn("'+' -> '-'", ops)
        self.assertIn("1 -> 2", ops)

    def test_python_ignores_docstring_and_comment(self):
        ms = mutate.mutants(PY, "python")
        self.assertTrue(ms and all(m["line"] == 4 for m in ms))

    def test_deterministic(self):
        self.assertEqual(mutate.mutants(ZEHN, "zehn"), mutate.mutants(ZEHN, "zehn"))


class ReplyTests(unittest.TestCase):
    def test_parse(self):
        r = review.parse_reply('noise {"verdict": "Defect", "line": 7, "why": "sign"} tail')
        self.assertEqual((r["verdict"], r["line"]), ("defect", 7))
        self.assertIsNone(review.parse_reply("I think it is fine")["verdict"])
        self.assertEqual(review.parse_reply('{"verdict": "correct", "line": null}')["verdict"], "correct")

    def test_score(self):
        item = {"kind": "mutated", "shown_line": 10}
        self.assertEqual(review.score(item, {"verdict": "defect", "line": 11}),
                         {"correct": True, "located": True, "answered": True})
        self.assertFalse(review.score(item, {"verdict": "defect", "line": 20})["located"])
        self.assertFalse(review.score(item, {"verdict": "correct", "line": None})["correct"])
        self.assertTrue(review.score({"kind": "clean", "shown_line": None}, {"verdict": "correct", "line": None})["correct"])
        self.assertFalse(review.score(item, {"verdict": None, "line": None})["answered"])


class Items(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = schema.load_tasks([os.path.join(HERE, "tasks")], ["pure_001", "effect_001"])
        cls.items = review.build_items(cls.tasks, workers=2)

    def test_shape(self):
        self.assertGreaterEqual(len(self.items), 6)
        for i in self.items:
            self.assertEqual(i["kind"] == "mutated", i["mutation"] is not None)
        arms = {i["arm"] for i in self.items}
        self.assertEqual(arms, set(review.ARMS))

    def test_mutated_line_points_at_the_change(self):
        by = {i["item_id"]: i for i in self.items}
        for i in self.items:
            if i["kind"] != "mutated":
                continue
            clean = by[i["item_id"].replace(":mutated", ":clean")]["code"].split("\n")
            mut = i["code"].split("\n")
            diff = [n + 1 for n, (a, b) in enumerate(zip(clean, mut)) if a != b]
            self.assertEqual(diff, [i["shown_line"]], i["item_id"])

    def test_python_examples_arm_shows_the_examples_only_there(self):
        for i in self.items:
            self.assertEqual("Visible examples" in i["code"], i["arm"] == "python_examples")
            self.assertEqual("intent" in i["code"], i["arm"] == "zehn")

    def test_deterministic(self):
        again = review.build_items(self.tasks, workers=2)
        self.assertEqual(again, self.items)


class Fake:
    """Says 'defect' for everything."""
    def complete(self, system, messages, temperature, ctx):
        return {"text": '{"verdict": "defect", "line": null, "why": "x"}', "in_tokens": 10, "out_tokens": 5}


class RunReport(unittest.TestCase):
    def test_run_resume_and_report(self):
        tasks = schema.load_tasks([os.path.join(HERE, "tasks")], ["pure_001", "effect_001"])
        items = review.build_items(tasks, workers=2)
        with tempfile.TemporaryDirectory() as d:
            items_path = os.path.join(d, "items.json")
            json.dump({"items": items}, open(items_path, "w"))
            argv = ["run", "--items", items_path, "--model", "stub:x", "--repeats", "2", "--out", d,
                    "--run-id", "r", "--tasks-dir", os.path.join(HERE, "tasks")]
            args = review_cli.build_parser().parse_args(argv)
            self.assertEqual(review_cli.cmd_run(args, client=Fake()), 0)
            recs = review_cli.load_records(os.path.join(d, "r"))
            self.assertEqual(len(recs), 2 * len(items))
            self.assertEqual(review_cli.cmd_run(args, client=Fake()), 0)       # resume: nothing new
            self.assertEqual(len(review_cli.load_records(os.path.join(d, "r"))), 2 * len(items))
            s = review_cli.summarize(recs)
            self.assertAlmostEqual(s["zehn"]["detect"], 1.0)
            self.assertAlmostEqual(s["zehn"]["false_alarm"], 1.0)
            self.assertAlmostEqual(s["zehn"]["accuracy"], 0.5)
            p = review_cli.paired(recs, "zehn", "python")
            self.assertAlmostEqual(p["diff"], 0.0)


class Flaky:
    """The first call of every second item fails the way a Gemini 503 does after all retries."""
    def __init__(self):
        self.n = 0

    def complete(self, system, messages, temperature, ctx):
        self.n += 1
        if self.n % 2 == 0:
            from benchlib.models import ModelError
            raise ModelError("giving up after 6 attempts (HTTP 503)")
        return {"text": '{"verdict": "correct", "line": null, "why": ""}', "in_tokens": 1, "out_tokens": 1}


class Transient(unittest.TestCase):
    def test_failed_calls_are_recorded_then_redone(self):
        tasks = schema.load_tasks([os.path.join(HERE, "tasks")], ["pure_001", "effect_001"])
        items = review.build_items(tasks, workers=2)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "items.json")
            json.dump({"items": items}, open(p, "w"))
            argv = ["run", "--items", p, "--model", "stub:x", "--repeats", "1", "--out", d, "--run-id", "r",
                    "--tasks-dir", os.path.join(HERE, "tasks")]
            args = review_cli.build_parser().parse_args(argv)
            flaky = Flaky()
            self.assertEqual(review_cli.cmd_run(args, client=flaky), 0)      # no fatal error
            recs = review_cli.load_records(os.path.join(d, "r"))
            self.assertEqual(len(recs), len(items))
            self.assertTrue(any(r["error"] for r in recs))
            flaky.n = 1                                                       # next call ok, then 1 in 2 fails
            for _ in range(10):
                review_cli.cmd_run(args, client=flaky)
                if not any(r["error"] for r in review_cli.load_records(os.path.join(d, "r"))):
                    break
            final = review_cli.load_records(os.path.join(d, "r"))
            self.assertEqual(len(final), len(items))
            self.assertFalse(any(r["error"] for r in final))
            self.assertTrue(os.path.exists(os.path.join(d, "r", "records.errors.jsonl")))


class Committed(unittest.TestCase):
    def test_committed_items_are_consistent(self):
        path = os.path.join(HERE, "experiments", "review", "items.json")
        items = json.load(open(path))["items"]
        tasks = {i["task_id"] for i in items}
        self.assertGreaterEqual(len(tasks), 50)
        for t in tasks:
            self.assertEqual({i["arm"] for i in items if i["task_id"] == t}, set(review.ARMS))
        self.assertEqual(len(items), len(tasks) * len(review.ARMS) * 2)


if __name__ == "__main__":
    unittest.main()
