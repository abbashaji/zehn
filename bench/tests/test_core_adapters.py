from __future__ import annotations

import tempfile
import unittest

import _common as c
from benchlib import adapters, schema

TASK = schema.load_tasks([c.DEMO_ROOT])[0]
WRONG_PY = "def sum_above(xs, limit):\n    return sum(xs)\n"


def both(lang, code):
    ad = adapters.get(lang)
    with tempfile.TemporaryDirectory() as d:
        return ad.tool_check(TASK, code, d), ad.run_hidden(TASK, code, TASK["_tests"], d)


class AdapterTests(unittest.TestCase):
    def test_registry(self):
        self.assertTrue({"zehn", "python_plain", "python_strict"} <= set(adapters.REGISTRY))

    def test_zehn(self):
        chk, res = both("zehn", c.read(c.DEMO_DIR, "ref.zehn"))
        self.assertTrue(chk["ok"], chk)
        self.assertEqual((res["passed"], res["total"]), (8, 8))
        chk, res = both("zehn", c.read(c.FIXTURES, "wrong_sum_above.zehn"))
        self.assertLess(res["passed"], 8)

    def test_zehn_tool_maps_diagnostics(self):
        chk, res = both("zehn", "fn sum_above(xs: List<Int>, limit: Int) -> Int\n  example sum_above([], 0) == 0\ndo\n  return nope(xs)\nend fn\n")
        self.assertFalse(chk["ok"])
        d = [x for x in chk["diagnostics"] if x["code"] == "E0302"]
        self.assertTrue(d and d[0]["unknown_name"] and isinstance(d[0]["line"], int))
        self.assertEqual(res["passed"], 0)
        chk, res = both("zehn", "fn broken(\n")
        self.assertFalse(chk["ok"])
        self.assertEqual(res["passed"], 0)

    def test_zehn_layout_only_error_is_forgiven(self):
        ok_src = c.read(c.DEMO_DIR, "ref.zehn")
        ugly = ok_src.replace("\n  ", "\n      ", 1) if "\n  " in ok_src else ok_src + "\n\n\n"
        ad = adapters.get("zehn")
        self.assertNotEqual(ugly, ok_src)
        with tempfile.TemporaryDirectory() as d:
            raw = ad._check(ad._write(ugly, d))
            self.assertIn("E0203", [x["code"] for x in raw["diagnostics"]], raw)   # the strict tool does reject it
            chk = ad.tool_check(TASK, ugly, d)
            self.assertTrue(chk["ok"], chk)
            self.assertEqual([x["code"] for x in chk["diagnostics"]], ["W0301"])
            self.assertEqual(ad.run_hidden(TASK, ugly, TASK["_tests"], d)["passed"], 8)

    def test_zehn_layout_error_hidden_when_real_error_remains(self):
        bad = "fn sum_above(xs: List<Int>, limit: Int) -> Int\n    example sum_above([], 0) == 0\ndo\n        return nope(xs)\nend fn\n"
        with tempfile.TemporaryDirectory() as d:
            chk = adapters.get("zehn").tool_check(TASK, bad, d)
        codes = [x["code"] for x in chk["diagnostics"]]
        self.assertFalse(chk["ok"])
        self.assertIn("E0302", codes)
        self.assertNotIn("E0203", codes)

    def test_python_plain(self):
        chk, res = both("python_plain", c.read(c.DEMO_DIR, "ref.py"))
        self.assertTrue(chk["ok"], chk)
        self.assertEqual((res["passed"], res["total"]), (8, 8))
        chk, res = both("python_plain", WRONG_PY)
        self.assertLess(res["passed"], 8)
        self.assertFalse(chk["ok"])   # the visible example catches it
        self.assertEqual(chk["diagnostics"][0]["code"], "ExampleFail")

    def test_python_plain_unknown_name_and_syntax(self):
        chk, _ = both("python_plain", "def sum_above(xs, limit):\n    return summ(xs)\n")
        codes = {d["code"]: d for d in chk["diagnostics"]}
        self.assertTrue(codes["NameError"]["unknown_name"])
        chk, res = both("python_plain", "def broken(:\n")
        self.assertEqual(chk["diagnostics"][0]["code"], "SyntaxError")
        self.assertEqual(res["passed"], 0)

    @unittest.skipUnless(adapters.get("python_strict").available()[0], "mypy and ruff not installed")
    def test_python_strict(self):
        chk, res = both("python_strict", c.read(c.DEMO_DIR, "ref.py"))
        self.assertTrue(chk["ok"], chk)
        self.assertEqual((res["passed"], res["total"]), (8, 8))
        chk, res = both("python_strict", WRONG_PY)
        self.assertLess(res["passed"], 8)

    @unittest.skipUnless(adapters.get("python_strict").available()[0], "mypy and ruff not installed")
    def test_strict_rejects_type_error_that_plain_accepts(self):
        code = c.read(c.FIXTURES, "typeerr_sum_above.py")
        plain, res = both("python_plain", code)
        self.assertTrue(plain["ok"], plain)
        self.assertEqual(res["passed"], 8)
        strict, _ = both("python_strict", code)
        self.assertFalse(strict["ok"])
        self.assertIn("assignment", [d["code"] for d in strict["diagnostics"]])

    @unittest.skipUnless(adapters.get("python_strict").available()[0], "mypy and ruff not installed")
    def test_strict_unknown_name_flags(self):
        chk, _ = both("python_strict", "def sum_above(xs: list, limit: int) -> int:\n    return summ(xs)\n")
        flagged = [d for d in chk["diagnostics"] if d["unknown_name"]]
        self.assertTrue(flagged, chk["diagnostics"])

    def test_python_records_options_results(self):
        task = dict(TASK)
        task["types"] = [{"name": "Pt", "fields": [{"name": "x", "type": "Int"}, {"name": "y", "type": "Int"}]}]
        task["params"] = [{"name": "p", "type": "Pt"}, {"name": "k", "type": "Int"}]
        task["returns"] = "Result<Option<Pt>, Text>"
        task["entry"] = "f"
        code = ("from dataclasses import dataclass\nfrom typing import Optional\n"
                "from bench_prelude import Ok, Err, Result\n\n\n@dataclass\nclass Pt:\n    x: int\n    y: int\n\n\n"
                "def f(p: Pt, k: int) -> Result[Optional[Pt]]:\n"
                "    if k < 0:\n        return Err('neg')\n"
                "    if k == 0:\n        return Ok(None)\n"
                "    return Ok(Pt(p.x + k, p.y))\n")
        tests = [{"args": [{"x": 1, "y": 2}, 3],
                  "expect": {"$": "ok", "args": [{"$": "some", "args": [{"y": 2, "x": 4}]}]}},
                 {"args": [{"x": 1, "y": 2}, 0], "expect": {"$": "ok", "args": [{"$": "none"}]}},
                 {"args": [{"x": 1, "y": 2}, -1], "expect": {"$": "err", "args": ["neg"]}},
                 {"args": [{"x": 1, "y": 2}, 1], "expect": {"$": "err", "args": ["neg"]}}]
        with tempfile.TemporaryDirectory() as d:
            res = adapters.get("python_plain").run_hidden(task, code, tests, d)
        self.assertEqual((res["passed"], res["total"]), (3, 4))
        self.assertEqual(res["failures"][0]["index"], 3)

    def test_console_effect_python_and_zehn(self):
        task = dict(TASK)
        task["effects"] = ["console"]
        task["entry"] = "hello"
        task["params"] = [{"name": "n", "type": "Text"}]
        task["returns"] = "Int"
        tests = [{"args": ["ab"], "expect": 2, "stdout": "hi ab\n"}, {"args": [""], "expect": 0, "stdout": "hi \n"}]
        py = "def hello(n):\n    print('hi ' + n)\n    return len(n)\n"
        zh = ("fn hello(n: Text) -> Int\n  uses [console]\n  example text.len(\"\") == 0\ndo\n"
              "  let u = console.print(text.concat(\"hi \", n))\n  return text.len(n)\nend fn\n")
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(adapters.get("python_plain").run_hidden(task, py, tests, d)["passed"], 2)
            bad = py.replace("hi ", "yo ")
            self.assertEqual(adapters.get("python_plain").run_hidden(task, bad, tests, d)["passed"], 0)
            self.assertEqual(adapters.get("zehn").run_hidden(task, zh, tests, d)["passed"], 2)

    def test_zehn_dialect_variant_reaches_fmt_and_the_hidden_test_runner(self):
        # merge of TASK 06a: a program that uses a dialect's syntax must be formatted, checked and run
        # under that dialect, or the A/B scores the variant against a parser that rejects its own syntax
        src = ("fn double(n: Int) -> Int\n  example double(4) == 8\ndo\n  return n * 2\nend fn\n\n"
               "fn age(born: Int) -> Int\n  uses [time.now]\n  example age(1900) == 126 with time.now = mock [2026]\n"
               "do\n  return time.now() - born\nend fn\n")
        task = dict(TASK)
        task["entry"], task["params"], task["returns"], task["effects"] = "double", [{"name": "n", "type": "Int"}], "Int", []
        tests = [{"args": [4], "expect": 8}, {"args": [0], "expect": 0}]
        with tempfile.TemporaryDirectory() as d:
            plain = adapters.get("zehn")
            self.assertEqual(plain.run_hidden(task, src, tests, d)["passed"], 0)       # default dialect: E0201
            self.assertIsNone(plain._canonical(src, d))
            mock = adapters.get("zehn")
            mock.set_variant([("effect_examples", "mock")])
            self.assertEqual(mock.run_hidden(task, src, tests, d)["passed"], 2)
            self.assertEqual(mock._canonical(src, d), src)
            chk = mock.tool_check(task, src, d)
            self.assertTrue(chk["ok"], chk)


if __name__ == "__main__":
    unittest.main()
