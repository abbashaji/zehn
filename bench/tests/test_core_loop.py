from __future__ import annotations

import unittest

import _common as c
from benchlib import adapters, loop, schema
from benchlib.models import get_model, ModelError


class ScriptedModel:
    """Returns the queued replies in order (the last one repeats)."""
    name = "test:scripted"

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def complete(self, system, messages, temperature, ctx):
        self.calls.append([m["content"] for m in messages])
        text = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        return {"text": text, "in_tokens": 10, "out_tokens": 5}


def run(lang, model, rounds=5):
    task = schema.load_tasks([c.DEMO_ROOT])[0]
    ad = adapters.get(lang)
    ref = c.read(c.DEMO_DIR, "ref" + ad.ext)
    return loop.run_one(ad, task, model, run_id="t", set_label="dev", variant="default", repeat=1,
                        temperature=1.0, max_rounds=rounds, ref_code=ref), task


class LoopTests(unittest.TestCase):
    def test_perfect_accepted_round_1(self):
        for lang in ("zehn", "python_plain"):
            rec, _ = run(lang, get_model("stub:perfect"))
            self.assertEqual(schema.validate_record(rec), [], lang)
            self.assertEqual(rec["accepted_round"], 1)
            self.assertTrue(rec["first_try_pass"] and rec["final_pass"])
            self.assertEqual(rec["final_tests"], {"passed": 8, "total": 8})
            self.assertEqual(len(rec["rounds"]), 1)

    def test_broken_then_fixed_accepted_round_2(self):
        for lang in ("zehn", "python_plain"):
            rec, _ = run(lang, get_model("stub:broken_then_fixed"))
            self.assertEqual(schema.validate_record(rec), [], lang)
            self.assertEqual(rec["accepted_round"], 2)
            self.assertFalse(rec["first_try_pass"])
            self.assertTrue(rec["final_pass"])
            self.assertFalse(rec["rounds"][0]["tool_ok"])
            self.assertTrue(rec["rounds"][1]["tool_ok"])
            self.assertGreater(rec["total_in_tokens"], 0)

    def test_never_valid_is_not_accepted(self):
        for lang in ("zehn", "python_plain"):
            rec, _ = run(lang, get_model("stub:never_valid"), rounds=3)
            self.assertEqual(schema.validate_record(rec), [], lang)
            self.assertIsNone(rec["accepted_round"])
            self.assertFalse(rec["final_pass"])
            self.assertFalse(rec["first_try_pass"])
            self.assertEqual(len(rec["rounds"]), 3)
            self.assertEqual(rec["rounds"][0]["diag_codes"], ["NOCODE"])
            self.assertEqual(rec["final_tests"], {"passed": 0, "total": 8})

    def test_silent_bug_is_visible(self):
        # the tool accepts a program that is wrong: accepted but not final_pass
        wrong = "```py\ndef sum_above(xs, limit):\n    return sum(xs)\n```"
        model = ScriptedModel(wrong.replace("sum(xs)", "sum(xs)  # no check"))
        task = schema.load_tasks([c.DEMO_ROOT])[0]
        task = dict(task)
        task["visible_examples"] = [{"args": [[1], 0], "expect": 1}]   # the visible example hides the bug
        rec = loop.run_one(adapters.get("python_plain"), task, model, run_id="t", set_label="dev",
                           variant="default", repeat=1, temperature=1.0, max_rounds=5, ref_code="")
        self.assertEqual(rec["accepted_round"], 1)
        self.assertFalse(rec["final_pass"])

    def test_repair_turn_carries_tool_json(self):
        model = ScriptedModel("```zehn\nfn broken(\n```", c.read(c.DEMO_DIR, "ref.zehn").join(["```zehn\n", "```"]))
        rec, _ = run("zehn", model)
        self.assertEqual(rec["accepted_round"], 2)
        second = model.calls[1]
        self.assertEqual(len(second), 3)
        self.assertIn('"diagnostics"', second[2])
        self.assertTrue(second[2].endswith(loop.FIX_REQUEST))

    def test_last_code_block_wins_and_prompt_hides_notes(self):
        self.assertEqual(loop.extract_code("a\n```x\none\n```\nb\n```py\ntwo\n```\n"), "two\n")
        self.assertIsNone(loop.extract_code("no fences"))
        task = schema.load_tasks([c.DEMO_ROOT])[0]
        prompt = loop.task_prompt(task, None, ".zehn")
        self.assertNotIn(task["notes"], prompt)
        self.assertIn("sum_above(xs: List<Int>, limit: Int) -> Int", prompt)

    def test_model_failure_is_recorded(self):
        class Boom:
            name = "test:boom"

            def complete(self, *a):
                raise ModelError("nope")
        rec, _ = run("python_plain", Boom())
        self.assertEqual(schema.validate_record(rec), [])
        self.assertIn("nope", rec["error"])
        self.assertIsNone(rec["accepted_round"])
        self.assertFalse(rec["final_pass"])

    def test_variant_parsing(self):
        self.assertEqual(loop.parse_variant("default"), [])
        self.assertEqual(loop.parse_variant("a=b,c=d"), [("a", "b"), ("c", "d")])
        with self.assertRaises(ValueError):
            loop.parse_variant("oops")


if __name__ == "__main__":
    unittest.main()
