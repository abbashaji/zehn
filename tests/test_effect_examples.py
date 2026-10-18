"""TASK 06a: examples of effectful functions with a mock handler (dialect effect_examples=mock)."""
from __future__ import annotations

import ast
import glob
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import zehn  # noqa: E402  (imports zehnlib, which registers the flag and the explain texts)
from zehnlib import dialect, errors  # noqa: E402
from zehnlib.fmt import format_program  # noqa: E402
from zehnlib.interp import Interp  # noqa: E402
from zehnlib.parser import parse  # noqa: E402
from zehnlib.passes import effect_examples  # noqa: E402

MOCK = {"effect_examples": "mock"}
DIALECT_DIR = os.path.join(ROOT, "dialects", "effect_examples=mock")
GOOD = os.path.join(DIALECT_DIR, "examples", "greet_mock.zehn")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def codes(src, strict=True, dia=MOCK, fuel=1_000_000):
    """Every error/warning code of the analysis, failed examples included."""
    _, diags, exs = zehn.analyze(src, strict=strict, dialect=dia, fuel=fuel)
    return [d["code"] for d in diags] + [x["diag"]["code"] for x in exs if x["status"] == "fail"]


def example_results(src, strict=True, dia=MOCK, fuel=1_000_000):
    return zehn.analyze(src, strict=strict, dialect=dia, fuel=fuel)[2]


def cli(*args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py")] + list(args), cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return p.returncode, p.stdout


TWICE = ("fn twice() -> Int\n  uses [time.now]\n  example twice() == 3 with time.now = mock %s\n"
         "do\n  return time.now() + time.now()\nend fn\n")
GREET = ("fn greet(name: Text) -> Unit\n  uses [console]\n  example greet(\"Ada\") %s\n"
         "do\n  return console.print(text.concat(\"hello, \", name))\nend fn\n")


class FlagAndParse(unittest.TestCase):
    def test_flag_is_registered_default_off(self):
        self.assertEqual(dialect.get("effect_examples"), "off")
        self.assertEqual(dialect.active()["effect_examples"], "off")
        with self.assertRaises(errors.ZehnError):
            dialect.parse_cli(["effect_examples=maybe"])

    def test_flag_off_the_mock_clause_is_e0201(self):
        src = read(GOOD)
        _, diags, _ = zehn.analyze(src, strict=True)
        self.assertEqual([d["code"] for d in diags], ["E0201"])
        rc, out = cli("check", GOOD, "--strict")
        self.assertEqual(rc, 1)
        self.assertIn("E0201", out)

    def test_default_check_of_effects_example_is_unchanged(self):
        rc, out = cli("check", os.path.join("examples", "effects.zehn"))
        self.assertEqual(rc, 0)
        self.assertEqual(out, (
            "WARNING W0101 [log_line, line 2]: function 'log_line' has no example\n"
            "    hint   : add at least one `example` clause\n"
            "WARNING W0101 [greet, line 8]: function 'greet' has no example\n"
            "    hint   : add at least one `example` clause\n"
            "WARNING W0101 [stamp, line 14]: function 'stamp' has no example\n"
            "    hint   : add at least one `example` clause\n"
            "OK: 0 error(s), 1 example(s) passed, 0 failed\n"))

    def test_clause_nodes_are_empty_under_the_default_dialect(self):
        prog = parse("fn f() -> Int\n  example f() == 1\ndo\n  return 1\nend fn\n")
        cl = prog.funcs["f"].examples[0]
        self.assertEqual((cl.mocks, cl.prints), ([], None))

    def test_malformed_tails_are_parse_errors(self):
        for tail in ("with console", "with console = [1]", "with console = mock 1", "prints 1"):
            with self.subTest(tail=tail):
                src = "fn f() -> Int\n  example f() == 1 %s\ndo\n  return 1\nend fn\n" % tail
                self.assertEqual(codes(src), ["E0201"])


class GoodProgram(unittest.TestCase):
    def test_greet_mock_passes_strict_with_nothing_granted(self):
        _, diags, exs = zehn.analyze(read(GOOD), strict=True, dialect=MOCK)
        self.assertEqual(diags, [])
        self.assertEqual([x["status"] for x in exs], ["pass"] * 5)

    def test_cli_exit_codes(self):
        self.assertEqual(cli("check", GOOD, "--dialect", "effect_examples=mock", "--strict")[0], 0)
        self.assertEqual(cli("fmt", GOOD, "--check", "--dialect", "effect_examples=mock")[0], 0)

    def test_mock_does_not_leak_into_a_later_run(self):
        prog, _, _ = zehn.analyze(read(GOOD), strict=True, dialect=MOCK)
        it = Interp(prog)
        self.assertIsNone(it.mock)
        it.run_examples()
        self.assertIsNone(it.mock)
        with self.assertRaises(errors.ZehnError) as cm:      # a real run still needs the grant
            it.invoke(prog.funcs["age"], [1900])
        self.assertEqual(cm.exception.diag["code"], "E0604")


class Errors(unittest.TestCase):
    def test_dialect_error_programs_show_their_codes(self):
        want = {"bad_mock_cover.zehn": "E0605", "bad_mock_exhausted.zehn": "E0606",
                "bad_mock_type.zehn": "E0607"}
        for name, code in want.items():
            with self.subTest(name=name):
                self.assertIn(code, codes(read(os.path.join(DIALECT_DIR, "errors", name))))

    def test_e0605_missing_extra_duplicate_and_prints(self):
        cases = {
            "missing": GREET % "== 1 with time.now = mock [1]",
            "none given but prints": GREET % "prints [\"hello, Ada\"]",
            "duplicate": TWICE % "[1, 2] with time.now = mock [3]",
            "prints without console": TWICE % "[1, 2] prints []",
            "extra": "fn f() -> Int\n  example f() == 1 with console = mock []\ndo\n  return 1\nend fn\n",
        }
        for name, src in cases.items():
            with self.subTest(name=name):
                self.assertIn("E0605", codes(src))

    def test_e0605_when_the_example_calls_two_effectful_functions(self):
        src = ("fn a() -> Int\n  uses [time.now]\n  example a() == 1 with time.now = mock [1]\ndo\n"
               "  return time.now()\nend fn\n\n"
               "fn b() -> Unit\n  uses [console]\n  example b() with console = mock []\ndo\n"
               "  return console.print(\"x\")\nend fn\n\n"
               "fn c() -> Bool\n  example a() == 1 and b() == b() with time.now = mock [1]\ndo\n"
               "  return true\nend fn\n")
        self.assertIn("E0605", codes(src))

    def test_e0606_is_a_runtime_failure_naming_function_blame_and_example(self):
        exs = example_results(TWICE % "[1]")
        self.assertEqual([x["status"] for x in exs], ["fail"])
        d = exs[0]["diag"]
        self.assertEqual((d["code"], d["blame"], d["location"]["fn"]), ("E0606", "caller", "twice"))
        self.assertEqual(d["via_example"]["fn"], "twice")
        self.assertEqual(codes(TWICE % "[1, 2]"), [])
        self.assertEqual(codes(TWICE % "[1, 2, 3]"), [])         # unused results are allowed

    def test_e0607_wrong_type_unit_effect_and_effect_without_functions(self):
        self.assertEqual(codes(TWICE % "[1, \"x\"]"), ["E0607"])
        self.assertEqual(codes(GREET % "with console = mock [1]"), ["E0607"])
        src = ("fn rd() -> Int\n  uses [fs.read]\n  example rd() == 1 with fs.read = mock [1]\ndo\n"
               "  return 1\nend fn\n")
        self.assertEqual(codes(src), ["E0607"])
        self.assertEqual(codes(src.replace("[1]", "[]")), [])

    def test_prints_mismatch_is_e0401_with_both_sequences(self):
        exs = example_results(GREET % "with console = mock [] prints [\"bye\"]")
        d = exs[0]["diag"]
        self.assertEqual(d["code"], "E0401")
        self.assertEqual(d["values"]["printed"], '["hello, Ada"]')
        self.assertEqual(d["values"]["expected printed"], '["bye"]')
        self.assertEqual(codes(GREET % "with console = mock [] prints [\"hello, Ada\"]"), [])

    def test_prints_must_be_a_list_of_text(self):
        self.assertEqual(codes(GREET % "with console = mock [] prints [1]"), ["E0306"])

    def test_false_mocked_example_reports_left_and_right_from_a_replay(self):
        exs = example_results(TWICE.replace("== 3", "== 4") % "[1, 2]")
        d = exs[0]["diag"]
        self.assertEqual((d["code"], d["values"]["left"], d["values"]["right"]), ("E0401", "3", "4"))

    def test_unmocked_unit_example_is_still_impure(self):
        src = "fn f() -> Unit\n  uses [console]\n  example f()\ndo\n  return console.print(\"x\")\nend fn\n"
        self.assertEqual(codes(src), ["E0602"])      # (the type checker skips a function with errors)


class PurityAndStrict(unittest.TestCase):
    def test_e0602_still_applies_without_a_mock_in_contracts_and_for_direct_calls(self):
        unmocked = TWICE.replace(" with time.now = mock %s", "")
        self.assertIn("E0602", codes(unmocked))
        req = ("fn g() -> Int\n  uses [time.now]\n  requires g() == 1 with time.now = mock [1]\n"
               "  example g() == 1\ndo\n  return 1\nend fn\n")
        self.assertIn("E0201", codes(req))                      # the clause exists only on examples
        ens = ("fn h() -> Int\n  uses [time.now]\n  ensures h() == 1\n  example h() == 1 with time.now = mock [1]\n"
               "do\n  return time.now()\nend fn\n")
        self.assertIn("E0602", codes(ens))
        direct = "fn d() -> Int\n  uses [time.now]\n  example time.now() == 1 with time.now = mock [1]\ndo\n  return 1\nend fn\n"
        self.assertIn("E0602", codes(direct))

    def test_mock_list_items_are_pure(self):
        src = ("fn a() -> Int\n  uses [time.now]\n  example a() == 1 with time.now = mock [a()]\ndo\n"
               "  return time.now()\nend fn\n")
        self.assertIn("E0602", codes(src))

    def test_a_mocked_example_satisfies_the_strict_rule_for_an_effectful_function(self):
        no_example = "fn t() -> Int\n  uses [time.now]\ndo\n  return time.now()\nend fn\n"
        self.assertEqual(codes(no_example), ["E0402"])
        self.assertEqual(codes(no_example.replace("do\n", "  example t() == 5 with time.now = mock [5]\ndo\n", 1)), [])

    def test_literal_strict_switch(self):
        pure_only = ("fn p() -> Int\n  example p() == 1\ndo\n  return 1\nend fn\n\n"
                     "fn t() -> Int\n  uses [time.now]\n  example p() == 1\ndo\n  return time.now()\nend fn\n")
        self.assertFalse(effect_examples.STRICT_NEEDS_MOCKED_EXAMPLE)
        self.assertEqual(codes(pure_only), [])
        with mock.patch.object(effect_examples, "STRICT_NEEDS_MOCKED_EXAMPLE", True):
            self.assertEqual(codes(pure_only), ["E0402"])
            self.assertEqual(codes(pure_only, strict=False), [])
            self.assertEqual(codes(read(GOOD)), [])


class FormatAndFuel(unittest.TestCase):
    def test_fmt_is_idempotent_and_sorts_clauses_by_effect(self):
        src = ("fn r(b: Int) -> Int\n  uses [console, time.now]\n"
               "  example r(1) == 1 with time.now = mock [2] with console = mock [] prints [\"x\"]\ndo\n"
               "  console.print(\"x\")\n  return time.now() - b\nend fn\n")
        with dialect.using(MOCK):
            once = format_program(parse(src))
            twice = format_program(parse(once))
        self.assertEqual(once, twice)
        self.assertIn("example r(1) == 1 with console = mock [] with time.now = mock [2] prints [\"x\"]", once)
        self.assertEqual(codes(src), ["E0203"])                  # not canonical under --strict
        self.assertEqual(codes(once), [])

    def test_good_program_round_trips(self):
        with dialect.using(MOCK):
            self.assertEqual(format_program(parse(read(GOOD))), read(GOOD))

    def test_mocked_examples_are_charged_like_any_example(self):
        def least_fuel(src):
            for n in range(1, 200):
                exs = example_results(src, fuel=n)
                if exs[0]["status"] == "pass":
                    return n
                self.assertEqual(exs[0]["diag"]["code"], "E0801")
            self.fail("no fuel up to 200 was enough")

        one, four = least_fuel(TWICE % "[1, 2]"), least_fuel(TWICE % "[1, 2, 3, 4, 5]")
        self.assertEqual(four - one, 3)                          # each extra list item is one step
        exs = example_results(TWICE % "[1, 2]", fuel=3)
        self.assertEqual(exs[0]["diag"]["via_example"]["fn"], "twice")


class Artifacts(unittest.TestCase):
    def test_dialect_folder_files_are_canonical_and_the_good_ones_pass_strict(self):
        for path in glob.glob(os.path.join(DIALECT_DIR, "*", "*.zehn")):
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertEqual(cli("fmt", path, "--check", "--dialect", "effect_examples=mock")[0], 0)
        for path in glob.glob(os.path.join(DIALECT_DIR, "examples", "*.zehn")):
            self.assertEqual(codes(read(path)), [], path)

    def test_explain_texts_are_registered(self):
        for code in ("E0605", "E0606", "E0607"):
            self.assertIn(code, errors.EXPLAIN)
            rc, out = cli("explain", code)
            self.assertEqual(rc, 0)
            self.assertIn("effect_examples=mock", out)

    def test_catalog_entries(self):
        for code in ("E0605", "E0606", "E0607"):
            base = os.path.join(ROOT, "catalog", code)
            meta = json.loads(read(os.path.join(base, "meta.json")))
            self.assertEqual(set(meta), {"strict", "dialect", "note"})
            self.assertEqual(meta["dialect"], MOCK)
            self.assertTrue(meta["strict"])
            self.assertIn(code, codes(read(os.path.join(base, "broken.zehn")), meta["strict"], meta["dialect"]))
            self.assertEqual(codes(read(os.path.join(base, "fixed.zehn")), meta["strict"], meta["dialect"]), [])

    def test_experiment_files(self):
        exp = json.loads(read(os.path.join(ROOT, "bench", "experiments", "effect_examples", "experiment.json")))
        ids = sorted(json.loads(read(p))["id"] for p in glob.glob(os.path.join(ROOT, "bench", "tasks", "effect", "*", "task.json")))
        self.assertEqual(exp, {"a": "default", "b": "effect_examples=mock", "tasks_dir": "bench/tasks",
                               "only": ids, "repeats": 5, "simpler": "a"})
        run_md = read(os.path.join(ROOT, "bench", "experiments", "effect_examples", "RUN.md"))
        for needle in ("--variant default", "--variant effect_examples=mock", "report.py ab"):
            self.assertIn(needle, run_md)
        self.assertLess(len(read(os.path.join(ROOT, "bench", "variants", "effect_examples=mock.md")).split()), 300)

    def test_spec_fragment_and_adr(self):
        frag = read(os.path.join(ROOT, "docs", "spec_fragments", "06a_effect_examples.md"))
        self.assertTrue(frag.startswith("Target: SPEC.md section "))
        self.assertIn("action: add", frag.splitlines()[0])
        adr = read(os.path.join(ROOT, "DECISIONS", "ADR-0019-effect-examples.md"))
        self.assertEqual(adr.splitlines()[1], "Status: measured")

    def test_new_python_files_parse_as_python_3_9_and_use_lf(self):
        for rel in ("zehnlib/passes/effect_examples.py", "tests/test_effect_examples.py"):
            with open(os.path.join(ROOT, rel), "rb") as fh:
                raw = fh.read()
            self.assertNotIn(b"\r", raw, rel)
            ast.parse(raw.decode("utf-8"), feature_version=(3, 9))
            self.assertIn("from __future__ import annotations", raw.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
