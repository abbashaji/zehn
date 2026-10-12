from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest

import _common as c
from benchlib import schema


def demo_task():
    return json.loads(c.read(c.DEMO_DIR, "task.json"))


def demo_tests():
    return json.loads(c.read(c.DEMO_DIR, "tests.json"))


class TaskValidation(unittest.TestCase):
    def test_accepts_demo(self):
        self.assertEqual(schema.validate_task(demo_task(), fixture=True), [])
        self.assertEqual(schema.validate_tests(demo_task(), demo_tests()), [])
        t = schema.load_tasks([c.DEMO_ROOT])
        self.assertEqual([x["id"] for x in t], ["demo_000"])
        self.assertEqual(len(t[0]["_tests"]), 8)

    def test_rejects_fewer_than_8_tests(self):
        errs = schema.validate_tests(demo_task(), demo_tests()[:7])
        self.assertTrue(any("at least 8" in e for e in errs), errs)

    def test_rejects_type_outside_allowed_set(self):
        for bad in ("Map<Int, Int>", "Option<Option<Int>>", "(Int, Int)", "Float", "Result<Int, Int>", "Unit"):
            t = demo_task()
            t["params"][1]["type"] = bad
            self.assertTrue(schema.validate_task(t, fixture=True), bad)
        t = demo_task()
        t["returns"] = "Shape"   # undeclared record
        self.assertTrue(schema.validate_task(t, fixture=True))

    def test_rejects_missing_entry(self):
        t = demo_task()
        del t["entry"]
        self.assertTrue(any("entry" in e for e in schema.validate_task(t, fixture=True)))

    def test_id_prefix_rule_outside_fixtures(self):
        self.assertTrue(schema.validate_task(demo_task(), fixture=False))   # demo_000 is not pure_NNN

    def test_value_checks(self):
        t = demo_tests()
        t[0]["args"][1] = True   # a Bool is not an Int
        self.assertTrue(schema.validate_tests(demo_task(), t))
        t = demo_tests()
        t[1]["expect"] = 2 ** 63   # does not fit 64-bit
        self.assertTrue(schema.validate_tests(demo_task(), t))
        t = demo_tests()
        t[2]["stdout"] = "x"   # stdout only with the console effect
        self.assertTrue(schema.validate_tests(demo_task(), t))

    def test_console_task_needs_stdout(self):
        task = demo_task()
        task["effects"] = ["console"]
        self.assertTrue(schema.validate_tests(task, demo_tests()))

    def test_records_and_options(self):
        task = demo_task()
        task["types"] = [{"name": "Item", "fields": [{"name": "n", "type": "Int"}, {"name": "tag", "type": "Option<Text>"}]}]
        task["params"][0]["type"] = "List<Item>"
        task["visible_examples"] = [{"args": [[{"n": 1, "tag": {"$": "none"}}], 0], "expect": 1}]
        self.assertEqual(schema.validate_task(task, fixture=True), [])
        recs = schema.record_map(task)
        ty = schema.parse_type("List<Item>", {"Item": 1})
        self.assertEqual(schema.check_value([{"n": 1, "tag": {"$": "none"}}], ty, recs), [])
        self.assertTrue(schema.check_value([{"n": 1}], ty, recs))

    def test_loader_skips_underscore_and_finds_two_levels(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            shutil.copytree(c.DEMO_DIR, os.path.join(d, "pure", "pure_001"))
            shutil.copytree(c.DEMO_DIR, os.path.join(d, "_hidden_fixture", "pure_002"))
            p = os.path.join(d, "pure", "pure_001", "task.json")
            t = json.loads(c.read(p))
            t["id"] = "pure_001"
            with open(p, "w") as f:
                json.dump(t, f)
            self.assertEqual([x["id"] for x in schema.load_tasks([d])], ["pure_001"])
            with self.assertRaises(schema.TaskError):
                schema.load_tasks([d], only=["pure_999"])


class RecordValidation(unittest.TestCase):
    def good(self):
        return {"schema": 1, "run_id": "r", "set": "dev", "task_id": "pure_001", "category": "pure",
                "kind": "write", "lang": "zehn", "variant": "default", "model": "stub:perfect", "repeat": 1,
                "temperature": 1.0,
                "rounds": [{"i": 1, "tool_ok": True, "diag_codes": [], "unknown_names": 0,
                            "in_tokens": 3, "out_tokens": 4}],
                "accepted_round": 1, "first_try_pass": True, "final_pass": True,
                "final_tests": {"passed": 8, "total": 8}, "total_in_tokens": 3, "total_out_tokens": 4,
                "wall_ms": 5, "error": None}

    def test_good_and_bad(self):
        self.assertEqual(schema.validate_record(self.good()), [])
        for mutate in (lambda r: r.pop("model"), lambda r: r.update(accepted_round=2),
                       lambda r: r.update(set="train"), lambda r: r["rounds"][0].pop("tool_ok"),
                       lambda r: r.update(final_tests={"passed": 9, "total": 8}),
                       lambda r: r.update(extra=1), lambda r: r.update(schema=2)):
            r = copy.deepcopy(self.good())
            mutate(r)
            self.assertTrue(schema.validate_record(r))


if __name__ == "__main__":
    unittest.main()
