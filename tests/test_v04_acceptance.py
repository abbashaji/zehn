"""TASK_08: the v0.4 decisions pinned (floor division kept and specified, effectful functions exempt
from the strict example rule, defaults unchanged) and the roadmap section 5 acceptance checks."""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
import unittest
from fractions import Fraction
from math import floor

from test_registry import ROOT

import zehn
from zehnlib import dialect
from zehnlib.errors import ZehnError


def run_fn(src, a, b):
    prog = zehn.parse(src)
    return zehn.Interp(prog).invoke(prog.funcs["f"], [a, b])


def src_for(op):
    return "fn f(a: Int, b: Int) -> Int\n  example f(7, 2) == %d\ndo\n  return a %s b\nend fn\n" % (
        3 if op == "/" else 1, op)


def codes(src, strict=False):
    _, diags, ex = zehn.analyze(src, strict=strict)
    return sorted({d["code"] for d in diags} | {x["diag"]["code"] for x in ex if x["status"] == "fail"})


GRID = [-9, -7, -6, -3, -2, -1, 0, 1, 2, 3, 6, 7, 9]
BIG = 3 ** 200


class DivisionDecision(unittest.TestCase):
    def test_defaults_are_unchanged(self):
        self.assertEqual(dialect.get("int_ops"), "operators")
        self.assertEqual(dialect.get("effect_examples"), "off")

    def test_floor_matches_an_exact_rational_floor(self):
        for a in GRID + [BIG, -BIG, 2 ** 70 + 3]:
            for b in GRID + [-(2 ** 33), 2 ** 33, BIG - 1]:
                if b == 0:
                    continue
                q = run_fn(src_for("/"), a, b)
                self.assertEqual(q, floor(Fraction(a, b)), (a, b))

    def test_remainder_identity_and_sign_of_the_divisor(self):
        for a in GRID + [BIG, -BIG]:
            for b in GRID + [-(2 ** 33), 2 ** 33]:
                if b == 0:
                    continue
                q, r = run_fn(src_for("/"), a, b), run_fn(src_for("%"), a, b)
                self.assertEqual(a, q * b + r, (a, b))
                if b > 0:
                    self.assertTrue(0 <= r < b, (a, b, r))
                else:
                    self.assertTrue(b < r <= 0 or r == 0, (a, b, r))

    def test_the_values_written_in_the_spec(self):
        spec = open(os.path.join(ROOT, "SPEC.md"), encoding="utf-8").read()
        for a, b, q, r in [(7, 2, 3, 1), (-7, 2, -4, 1), (7, -2, -4, -1), (-7, -2, 3, -1)]:
            self.assertEqual(run_fn(src_for("/"), a, b), q)
            self.assertEqual(run_fn(src_for("%"), a, b), r)
        for text in ("`-7 / 2 == -4`", "`7 / -2 == -4`", "`-7 / -2 == 3`", "`-7 % 2 == 1`", "`7 % -2 == -1`", "`-7 % -2 == -1`"):
            self.assertIn(text, spec)

    def test_zero_divisor_is_e0505_blaming_the_caller(self):
        for op in ("/", "%"):
            for a in (5, -5, 0, BIG):
                with self.assertRaises(ZehnError) as cm:
                    run_fn(src_for(op), a, 0)
                self.assertEqual(cm.exception.diag["code"], "E0505", (op, a))
                self.assertEqual(cm.exception.diag.get("blame"), "caller", (op, a))

    def test_the_example_file_is_strict_clean_and_ran_its_examples(self):
        path = os.path.join(ROOT, "examples", "int_division.zehn")
        _, diags, ex = zehn.analyze(open(path, encoding="utf-8").read(), strict=True)
        self.assertEqual(diags, [])
        self.assertEqual(len(ex), 9)
        self.assertTrue(all(x["status"] == "pass" for x in ex))


class EffectExamplesDecision(unittest.TestCase):
    PURE = "fn p(x: Int) -> Int\n  intent \"id\"\ndo\n  return x\nend fn\n"
    EFFECT = ("fn g(t: Text) -> Unit\n  intent \"print\"\n  uses [console]\ndo\n  console.print(t)\n  return unit\n"
              "end fn\n")

    def test_a_pure_function_without_example_is_still_flagged(self):
        self.assertEqual(codes(self.PURE, strict=True), ["E0402"])
        _, diags, _ = zehn.analyze(self.PURE)
        self.assertEqual([d["code"] for d in diags], ["W0101"])

    def test_an_effectful_function_without_example_is_exempt(self):
        for strict in (False, True):
            _, diags, _ = zehn.analyze(self.EFFECT, strict=strict)
            self.assertNotIn("E0402", [d["code"] for d in diags])
            self.assertNotIn("W0101", [d["code"] for d in diags])

    def test_an_example_may_still_not_call_an_effectful_function(self):
        src = self.EFFECT.replace("do\n", "  example g(\"x\") == unit\ndo\n", 1)
        self.assertIn("E0602", codes(src))

    def test_spec_states_the_rule(self):
        spec = open(os.path.join(ROOT, "SPEC.md"), encoding="utf-8").read()
        self.assertIn("A *pure* function with zero examples", spec)
        self.assertIn("exempt from both", spec)


class Acceptance(unittest.TestCase):
    def test_every_example_is_strict_clean_and_has_no_recursion_false_positive(self):
        files = sorted(glob.glob(os.path.join(ROOT, "examples", "*.zehn")))
        self.assertGreaterEqual(len(files), 7)
        for path in files:
            _, diags, ex = zehn.analyze(open(path, encoding="utf-8").read(), strict=True)
            self.assertEqual(diags, [], path)
            self.assertTrue(all(x["status"] == "pass" for x in ex), path)

    def test_the_cli_agrees(self):
        for path in sorted(glob.glob(os.path.join(ROOT, "examples", "*.zehn"))):
            r = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py"), "check", path, "--strict"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, path + r.stdout + r.stderr)

    def test_spec_has_no_open_behaviour_left(self):
        spec = open(os.path.join(ROOT, "SPEC.md"), encoding="utf-8").read()
        self.assertTrue(spec.startswith("# Zehn (ذهن) — Language Specification v0.4"))
        self.assertNotRegex(spec, r"(?i)unspecified|not yet|should be pinned down")
        known = spec.split("## 12.")[1].split("## 13.")[0]
        self.assertNotRegex(known, r"(?i)unspecified|undefined|not yet|before v1")
        self.assertNotIn("Tuple types parse but have no expressions", spec)

    def test_version_strings(self):
        for rel in ("zehn.py", os.path.join("zehnlib", "cli.py")):
            head = open(os.path.join(ROOT, rel), encoding="utf-8").read(200)
            self.assertIn("Zehn v0.4", head)
        log = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
        self.assertRegex(log, r"(?m)^## v0\.4$")
        self.assertNotIn("v0.4 (in progress)", log)

    def test_adrs_carry_a_final_status_and_the_acceptance_adr_exists(self):
        d = os.path.join(ROOT, "DECISIONS")
        for name, word in (("ADR-0017-int-division.md", "decided"), ("ADR-0019-effect-examples.md", "decided"),
                           ("ADR-0010-int-division-floor.md", "decided")):
            text = open(os.path.join(d, name), encoding="utf-8").read()
            self.assertRegex(text, r"(?m)^Status: " + word)
        for name in ("ADR-0017-int-division.md", "ADR-0019-effect-examples.md"):
            self.assertIn("underpowered", open(os.path.join(d, name), encoding="utf-8").read())
        acc = glob.glob(os.path.join(d, "ADR-*-v04-acceptance.md"))
        self.assertEqual(len(acc), 1)
        text = open(acc[0], encoding="utf-8").read()
        for crit in ("baseline benchmark", "zero false positives", "no unspecified behaviour", "150 tests"):
            self.assertIn(crit, text)

    def test_the_baseline_is_published(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "bench", "BASELINE_v0.3.md")))


if __name__ == "__main__":
    unittest.main()
