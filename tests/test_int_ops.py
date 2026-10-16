"""TASK 06c: int.div_floor / int.div_trunc / int.rem_euclid and the dialect flag int_ops (E0312)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from test_registry import ROOT, Recording

import zehn
from zehnlib import dialect
from zehnlib.errors import EXPLAIN, ZehnError

EXPLICIT = {"int_ops": "explicit"}
BIG = 3 ** 200            # about 317 bits: above the 128-bit free zone
CASES = [(7, 2), (-7, 2), (7, -2), (-7, -2), (6, 3), (-6, 3), (6, -3), (-6, -3), (0, 5), (0, -5),
         (1, 7), (-1, 7), (1, -7), (-1, -7), (5, 1), (-5, 1), (5, -1), (-5, -1),
         (2 ** 70 + 3, -(2 ** 33)), (-(2 ** 70) - 3, 2 ** 33), (BIG, -7), (-BIG, 7), (-BIG, -BIG + 1)]


def call(name, a, b):
    src = ("fn f(a: Int, b: Int) -> Int\n  example f(7, 2) == %s\ndo\n  return int.%s(a, b)\nend fn\n"
           % ({"div_floor": 3, "div_trunc": 3, "rem_euclid": 1}[name], name))
    prog = zehn.parse(src)
    return zehn.Interp(prog).invoke(prog.funcs["f"], [a, b])


def fn_src(body, example="f(7, 2) == 3", requires=True):
    return ("fn f(a: Int, b: Int) -> Int\n%s  example %s\ndo\n  return %s\nend fn\n"
            % ("  requires b != 0\n" if requires else "", example, body))


def codes(src, dia=None):
    _, diags, ex = zehn.analyze(src, dialect=dia)
    return sorted({d["code"] for d in diags} | {x["diag"]["code"] for x in ex if x["status"] == "fail"})


def lines_of(src, dia):
    _, diags, _ = zehn.analyze(src, dialect=dia)
    return [d["location"]["line"] for d in diags if d["code"] == "E0312"]


def script(*args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py")] + list(args), cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return p.returncode, p.stdout


class Semantics(unittest.TestCase):
    def test_div_floor_matches_python_floor_division(self):
        for a, b in CASES:
            with self.subTest(a=a, b=b):
                self.assertEqual(call("div_floor", a, b), a // b)

    def test_div_trunc_rounds_toward_zero_with_integers_only(self):
        for a, b in CASES:
            with self.subTest(a=a, b=b):
                q = a // b                       # independent route: fix the floor quotient up
                if q < 0 and q * b != a:
                    q += 1
                got = call("div_trunc", a, b)
                self.assertEqual(got, q)
                self.assertLessEqual(abs(got * b), abs(a))            # never rounds away from zero
                self.assertLess(abs(a - got * b), abs(b))             # remainder is smaller than |b|
                self.assertTrue(a - got * b == 0 or (a - got * b < 0) == (a < 0))  # sign of dividend

    def test_rem_euclid_is_a_mod_abs_b(self):
        for a, b in CASES:
            with self.subTest(a=a, b=b):
                r = call("rem_euclid", a, b)
                self.assertEqual(r, a % abs(b))
                self.assertTrue(0 <= r < abs(b))
                self.assertEqual((a - r) % b, 0)

    def test_pinned_values(self):
        self.assertEqual([call("div_floor", -7, 2), call("div_trunc", -7, 2), call("rem_euclid", -7, 2)],
                         [-4, -3, 1])
        self.assertEqual([call("div_floor", 7, -2), call("div_trunc", 7, -2), call("rem_euclid", 7, -2)],
                         [-4, -3, 1])
        self.assertEqual([call("div_floor", -7, -2), call("div_trunc", -7, -2), call("rem_euclid", -7, -2)],
                         [3, 3, 1])

    def test_rem_euclid_differs_from_the_floor_remainder_for_a_negative_divisor(self):
        self.assertEqual(7 % -2, -1)
        self.assertEqual(call("rem_euclid", 7, -2), 1)

    def test_zero_divisor_is_e0505_blamed_on_the_caller(self):
        for name in ("div_floor", "div_trunc", "rem_euclid"):
            for a in (0, 5, -5, BIG):
                with self.subTest(name=name, a=a):
                    with self.assertRaises(ZehnError) as cm:
                        call(name, a, 0)
                    d = cm.exception.diag
                    self.assertEqual((d["code"], d["blame"]), ("E0505", "caller"))
                    self.assertEqual(d["message"], "division by zero")
                    self.assertEqual(d["location"], {"line": 4})

    def test_same_diagnostic_as_the_operator(self):
        prog = zehn.parse(fn_src("a / b", requires=False))
        with self.assertRaises(ZehnError) as op:
            zehn.Interp(prog).invoke(prog.funcs["f"], [1, 0])
        with self.assertRaises(ZehnError) as fn:
            call("div_floor", 1, 0)
        self.assertEqual(op.exception.diag["code"], fn.exception.diag["code"])
        self.assertEqual(op.exception.diag["fix_hint"], fn.exception.diag["fix_hint"])

    def test_registered_with_int_int_to_int(self):
        for name in ("div_floor", "div_trunc", "rem_euclid"):
            self.assertEqual(zehn.SIGS["int." + name], "(Int, Int) -> Int")
        self.assertEqual(codes("fn f(a: Int) -> Int\n  example f(1) == 1\ndo\n  return int.div_floor(a, true)\nend fn\n"),
                         ["E0306"])


class Fuel(unittest.TestCase):
    def used(self, body, a, b):
        prog = zehn.parse(fn_src(body, requires=False))
        it = Recording(prog)
        it.invoke(prog.funcs["f"], [a, b])
        return it.used, it.charges

    def test_small_operands_cost_the_same_as_the_operators(self):
        base, _ = self.used("a / b", 7, 2)
        self.assertEqual(self.used("int.div_floor(a, b)", 7, 2)[0], base)
        self.assertEqual(self.used("int.div_trunc(a, b)", 7, 2)[0], base)
        mod, _ = self.used("a % b", 7, 2)
        self.assertEqual(self.used("int.rem_euclid(a, b)", 7, 2)[0], mod)

    def test_big_operands_charge_wa_times_wb_like_the_operators(self):
        for a, b in [(BIG, 7), (7, BIG), (-BIG, BIG), (2 ** 200, 2 ** 130 + 1)]:
            wa, wb = (a.bit_length() >> 6) + 1, (b.bit_length() >> 6) + 1
            for op, fn in (("a / b", "int.div_floor(a, b)"), ("a / b", "int.div_trunc(a, b)"),
                           ("a % b", "int.rem_euclid(a, b)")):
                with self.subTest(a=a, b=b, fn=fn):
                    used_op, ch_op = self.used(op, a, b)
                    used_fn, ch_fn = self.used(fn, a, b)
                    self.assertEqual(used_fn, used_op)
                    self.assertEqual(ch_fn, ch_op)
                    self.assertIn(wa * wb, ch_fn)

    def test_charge_comes_before_the_zero_divisor_error(self):
        # a big dividend with a zero divisor still pays wa * wb first, as `/` does
        prog = zehn.parse(fn_src("int.div_floor(a, b)", requires=False))
        it = Recording(prog)
        with self.assertRaises(ZehnError):
            it.invoke(prog.funcs["f"], [BIG, 0])
        self.assertIn(((BIG.bit_length() >> 6) + 1) * 1, it.charges)

    def test_fuel_exhaustion_is_e0801_before_the_work(self):
        prog = zehn.parse(fn_src("int.div_trunc(a, b)"))
        it = zehn.Interp(prog, fuel=20)
        with self.assertRaises(ZehnError) as cm:
            it.invoke(prog.funcs["f"], [10 ** 3000, 3])
        self.assertEqual(cm.exception.diag["code"], "E0801")


class Flag(unittest.TestCase):
    def test_flag_is_registered_with_the_right_default(self):
        self.assertEqual(dialect.active()["int_ops"], "operators")
        self.assertEqual(dialect._FLAGS["int_ops"][1], ("operators", "explicit"))

    def test_default_dialect_accepts_the_operators(self):
        for body, ex in (("a / b", "f(7, 2) == 3"), ("a % b", "f(7, 2) == 1"),
                         ("(a + 1) / (b + 1)", "f(7, 2) == 2")):
            self.assertEqual(codes(fn_src(body, ex)), [])
            self.assertEqual(codes(fn_src(body, ex), {"int_ops": "operators"}), [])

    def test_explicit_rejects_both_operators(self):
        for body, op, ex in (("a / b", "/", "f(7, 2) == 3"), ("a % b", "%", "f(7, 2) == 1")):
            _, diags, _ = zehn.analyze(fn_src(body, ex), dialect=EXPLICIT)
            hits = [d for d in diags if d["code"] == "E0312"]
            self.assertEqual(len(hits), 1)
            self.assertIn("`%s`" % op, hits[0]["message"])
            for name in ("int.div_floor", "int.div_trunc", "int.rem_euclid"):
                self.assertIn(name, hits[0]["fix_hint"])
            self.assertEqual(hits[0]["severity"], "error")
            self.assertEqual(hits[0]["location"], {"fn": "f", "line": 5})

    def test_explicit_rejects_nested_expressions(self):
        self.assertEqual(lines_of(fn_src("a + (a / b) * 2 - a % b", "f(7, 2) == 8"), EXPLICIT), [5, 5])
        self.assertEqual(lines_of(fn_src("(a / b) / b", "f(7, 2) == 1"), EXPLICIT), [5, 5])
        self.assertEqual(lines_of(fn_src("int.abs(a / b)", "f(7, 2) == 3"), EXPLICIT), [5])
        self.assertEqual(lines_of(fn_src("int.max(1, 2 + a % (b + 1))", "f(7, 2) == 3"), EXPLICIT), [5])

    def test_explicit_rejects_the_operators_in_contracts_and_examples(self):
        src = ("fn f(a: Int, b: Int) -> Int\n  requires b != 0\n  requires a % b == 0 or a > 100\n"
               "  ensures out == a / b\n  example f(6, 2) == 6 / 2\ndo\n  return int.div_floor(a, b)\nend fn\n")
        self.assertEqual(codes(src), [])
        self.assertEqual(lines_of(src, EXPLICIT), [3, 4, 5])

    def test_explicit_in_if_match_and_loop_bodies(self):
        src = ("fn f(a: Int, b: Int) -> Int\n  requires b != 0\n  example f(7, 2) == 3\ndo\n"
               "  var t = 0\n  if a > 0 then\n    t := a / b\n  else\n    t := a % b\n  end if\n"
               "  return t\nend fn\n")
        self.assertEqual(codes(src), [])
        self.assertEqual(lines_of(src, EXPLICIT), [7, 9])

    def test_explicit_with_the_new_functions_is_clean_and_runs(self):
        src = fn_src("int.div_floor(a, b) + int.div_trunc(a, b) + int.rem_euclid(a, b)", "f(7, 2) == 7")
        self.assertEqual(codes(src, EXPLICIT), [])
        self.assertEqual(codes(src), [])

    def test_explicit_blocks_run_and_default_does_not(self):
        path = os.path.join(ROOT, "dialects", "int_ops=explicit", "errors", "bad_div.zehn")
        rc, out = script("check", path, "--dialect", "int_ops=explicit")
        self.assertEqual(rc, 1)
        self.assertIn("E0312", out)
        rc, out = script("check", path)
        self.assertEqual(rc, 0)
        self.assertNotIn("E0312", out)
        rc, out = script("check", path, "--json", "--dialect", "int_ops=explicit")
        self.assertIn("E0312", [d["code"] for d in json.loads(out)["diagnostics"]])

    def test_bad_flag_value_is_a_usage_error(self):
        path = os.path.join(ROOT, "dialects", "int_ops=explicit", "errors", "bad_div.zehn")
        rc, _ = script("check", path, "--dialect", "int_ops=floor")
        self.assertEqual(rc, 2)

    def test_dialect_state_does_not_leak_between_calls(self):
        zehn.analyze(fn_src("a / b"), dialect=EXPLICIT)
        self.assertEqual(dialect.get("int_ops"), "operators")
        self.assertEqual(codes(fn_src("a / b")), [])

    def test_explain_text(self):
        self.assertIn("int.div_trunc", EXPLAIN["E0312"])
        rc, out = script("explain", "E0312")
        self.assertEqual(rc, 0)
        self.assertIn("int.rem_euclid", out)

    def test_operators_keep_floor_semantics_by_default(self):
        prog = zehn.parse(fn_src("a / b", "f(-7, 2) == -4"))
        self.assertEqual(zehn.Interp(prog).run_examples()[0]["status"], "pass")


class Catalog(unittest.TestCase):
    def test_e0312_entry(self):
        d = os.path.join(ROOT, "catalog", "E0312")
        meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
        self.assertEqual(set(meta), {"strict", "dialect", "note"})
        dia = meta["dialect"]
        broken = open(os.path.join(d, "broken.zehn"), encoding="utf-8").read()
        fixed = open(os.path.join(d, "fixed.zehn"), encoding="utf-8").read()
        _, diags, ex = zehn.analyze(broken, strict=meta["strict"], dialect=dia)
        self.assertIn("E0312", [x["code"] for x in diags])
        _, diags, ex = zehn.analyze(fixed, strict=meta["strict"], dialect=dia)
        self.assertEqual([x for x in diags if x["severity"] == "error"], [])
        self.assertTrue(all(x["status"] == "pass" for x in ex))

    def test_dialect_programs_parse_and_are_canonical(self):
        base = os.path.join(ROOT, "dialects", "int_ops=explicit")
        for sub, want in (("examples", False), ("errors", True)):
            for name in sorted(os.listdir(os.path.join(base, sub))):
                src = open(os.path.join(base, sub, name), encoding="utf-8").read()
                prog = zehn.parse(src)
                self.assertEqual(zehn.format_program(prog), src, name)
                self.assertEqual("E0312" in codes(src, EXPLICIT), want, name)


if __name__ == "__main__":
    unittest.main()
