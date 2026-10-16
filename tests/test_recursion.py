"""E0311, unconditional recursion (zehnlib/passes/recursion.py)."""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import zehn  # noqa: E402
from zehnlib import errors, passes  # noqa: E402

ERR = os.path.join(ROOT, "errors")
CATALOG = os.path.join(ROOT, "catalog", "E0311")

CHK = ("fn chk(n: Int) -> Result<Int, Text>\n"
       "do\n"
       "  if n < 0 then\n"
       "    return err(\"neg\")\n"
       "  else\n"
       "    return ok(n)\n"
       "  end if\n"
       "end fn\n\n"
       "fn g2(a: Int, b: Int) -> Result<Int, Text>\n"
       "do\n"
       "  return ok(a + b)\n"
       "end fn\n\n")


def read(*p):
    with open(os.path.join(*p), encoding="utf-8") as fh:
        return fh.read()


def fn(name, body, params="n: Int", ret="Int"):
    """One function; `body` is the statements, already indented by two spaces."""
    return "fn %s(%s) -> %s\ndo\n%s\nend fn\n" % (name, params, ret, body)


def rfn(name, body):
    """A function returning Result<Int, Text>, for the `?` tests."""
    return fn(name, body, ret="Result<Int, Text>")


def program(*fns, prelude=""):
    return prelude + "\n".join(fns)


def e0311(src):
    prog = zehn.parse(src)
    return [d for d in zehn.static_diags(prog) if d["code"] == "E0311"]


def cycles_of(src):
    return [[c["fn"] for c in d["cycle"]] for d in e0311(src)]


def static_errors(src):
    return [d for d in zehn.static_diags(zehn.parse(src)) if d["severity"] == "error"]


class Flagged(unittest.TestCase):
    def test_self_loop(self):
        src = program(fn("f", "  return f(n + 1)"))
        ds = e0311(src)
        self.assertEqual(len(ds), 1)
        d = ds[0]
        self.assertEqual((d["code"], d["severity"], d["phase"]), ("E0311", "error", "check"))
        self.assertEqual(d["location"], {"fn": "f", "line": 3})
        self.assertEqual(d["cycle"], [{"fn": "f", "line": 3}])
        self.assertTrue(d["fix_hint"])

    def test_mutual_loop_is_one_diagnostic_in_call_order(self):
        src = program(fn("a", "  return b(n)"), fn("b", "\n  return a(n)"))
        ds = e0311(src)
        self.assertEqual(len(ds), 1)
        self.assertEqual([c["fn"] for c in ds[0]["cycle"]], ["a", "b"])
        self.assertEqual(ds[0]["location"]["fn"], "a")
        self.assertEqual([c["line"] for c in ds[0]["cycle"]], [3, 9])

    def test_three_cycle(self):
        src = program(fn("a", "  return b(n)"), fn("b", "  return c(n)"), fn("c", "  return a(n)"))
        self.assertEqual(cycles_of(src), [["a", "b", "c"]])

    def test_three_cycle_written_out_of_order_starts_at_first_function(self):
        src = program(fn("c", "  return a(n)"), fn("a", "  return b(n)"), fn("b", "  return c(n)"))
        self.assertEqual(cycles_of(src), [["c", "a", "b"]])

    def test_call_in_argument_of_an_unconditional_call(self):
        src = program(fn("f", "  return g2(n, f(n - 1))", ret="Result<Int, Text>").replace(
            "return g2(n, f(n - 1))", "return g2(n, f(n - 1)?)"), prelude=CHK)
        self.assertEqual(cycles_of(src), [["f"]])

    def test_call_nested_in_arithmetic_and_list_and_record(self):
        for body in ("  return 1 + f(n - 1)", "  return list.len([f(n)])",
                     "  let r = {a: f(n)}\n  return r.a", "  return 0 - f(n)",
                     "  let x = n + 1\n  let y = f(x)\n  return y",
                     "  var x = 0\n  x := f(n)\n  return x"):
            with self.subTest(body=body):
                self.assertEqual(cycles_of(program(fn("f", body))), [["f"]])

    def test_call_in_if_condition_and_match_subject(self):
        cond = "  if f(n) > 0 then\n    return 1\n  else\n    return 2\n  end if"
        subj = "  match f(n) do\n    case 0 =>\n      return 1\n    case _ =>\n      return 2\n  end match"
        self.assertEqual(cycles_of(program(fn("f", cond))), [["f"]])
        self.assertEqual(cycles_of(program(fn("f", subj))), [["f"]])

    def test_call_after_an_if_that_cannot_exit_early(self):
        body = "  var x = 0\n  if n > 0 then\n    x := 1\n  end if\n  return f(x)"
        self.assertEqual(cycles_of(program(fn("f", body))), [["f"]])

    def test_pipe_call_is_a_call(self):
        self.assertEqual(cycles_of(program(fn("f", "  return n |> f"))), [["f"]])

    def test_two_independent_cycles_are_two_diagnostics(self):
        src = program(fn("a", "  return a(n)"), fn("b", "  return c(n)"), fn("c", "  return b(n)"))
        self.assertEqual(cycles_of(src), [["a"], ["b", "c"]])

    def test_two_cycles_through_one_function_are_both_reported(self):
        src = program(fn("a", "  let x = b(n)\n  return c(x)"), fn("b", "  return a(n)"),
                      fn("c", "  return a(n)"))
        self.assertEqual(sorted(cycles_of(src)), [["a", "b"], ["a", "c"]])

    def test_function_that_calls_into_a_cycle_is_not_itself_reported(self):
        src = program(fn("entry", "  return spin(n)"), fn("spin", "  return spin(n)"))
        self.assertEqual(cycles_of(src), [["spin"]])


class NotFlagged(unittest.TestCase):
    def none(self, src):
        self.assertEqual(e0311(src), [])

    def test_base_case_in_if(self):
        self.none(program(fn("f", "  if n <= 0 then\n    return 0\n  else\n    return f(n - 1)\n  end if")))

    def test_call_only_in_then_branch(self):
        self.none(program(fn("f", "  if n < 0 then\n    return f(n + 1)\n  end if\n  return 0")))

    def test_call_under_match_case(self):
        body = "  match n do\n    case 0 =>\n      return 0\n    case _ =>\n      return f(n - 1)\n  end match"
        self.none(program(fn("f", body)))

    def test_call_under_and(self):
        body = "  if n > 0 and f(n - 1) > 0 then\n    return 1\n  else\n    return 0\n  end if"
        self.none(program(fn("f", body)))

    def test_call_under_or(self):
        body = "  if n < 0 or f(n - 1) > 0 then\n    return 1\n  else\n    return 0\n  end if"
        self.none(program(fn("f", body)))

    def test_call_under_implies(self):
        body = "  if n < 0 implies f(n - 1) > 0 then\n    return 1\n  else\n    return 0\n  end if"
        self.none(program(fn("f", body)))

    def test_call_after_try(self):
        body = "  let a = chk(n)?\n  return f(a)"
        self.none(program(rfn("f", body), prelude=CHK))

    def test_call_after_try_in_the_same_expression(self):
        self.none(program(rfn("f", "  return g2(chk(n)?, f(n)?)"), prelude=CHK))

    def test_call_after_try_in_an_earlier_if_condition(self):
        body = "  if chk(n)? > 0 then\n    return ok(1)\n  else\n    return ok(2)\n  end if"
        self.none(program(rfn("f", body), prelude=CHK).replace("return ok(2)", "return f(n)"))

    def test_call_after_try_in_a_short_circuit_right_operand(self):
        body = "  var x = 0\n  if n > 0 and chk(n)? > 0 then\n    x := 1\n  end if\n  return f(x)"
        self.none(program(rfn("f", body), prelude=CHK))

    def test_call_after_return(self):
        self.none(program(fn("f", "  return 0\n  return f(n)")))

    def test_call_after_an_if_that_returns(self):
        body = "  if n > 0 then\n    return 1\n  end if\n  return f(n + 1)"
        self.none(program(fn("f", body)))

    def test_call_after_a_match_that_returns(self):
        body = ("  match n do\n    case 0 =>\n      return 1\n    case _ =>\n      var x = 0\n"
                "      x := 1\n  end match\n  return f(n)")
        self.none(program(fn("f", body)))

    def test_function_mentioned_as_a_value(self):
        self.none(program(fn("f", "  return list.len(list.map([1, 2], f))")))
        self.none(program(fn("f", "  let g = f\n  return 0")))

    def test_contracts_and_examples_do_not_count(self):
        src = ("fn f(n: Int) -> Int\n  requires f(n) > 0\n  ensures f(n) > 0\n  example f(1) == f(2)\n"
               "do\n  return n\nend fn\n")
        self.none(src)

    def test_local_name_hides_the_function(self):
        self.none(program(fn("f", "  let g = 1\n  return g"), fn("g", "  return f(n)")))
        self.none(program(fn("f", "  return g(n)", params="g: Int"), fn("g", "  return f(n)")))

    def test_wrong_arity_is_not_an_edge(self):
        self.none(program(fn("f", "  return f(n, n)")))

    def test_acyclic_calls(self):
        self.none(program(fn("a", "  return b(n)"), fn("b", "  return c(n)"), fn("c", "  return n")))

    def test_conditional_mutual_recursion(self):
        body = "  if n <= 0 then\n    return 0\n  else\n    return %s(n - 1)\n  end if"
        self.none(program(fn("even", body % "odd"), fn("odd", body % "even")))

    def test_conditional_cycle_with_one_unconditional_edge(self):
        src = program(fn("a", "  return b(n)"),
                      fn("b", "  if n <= 0 then\n    return 0\n  else\n    return a(n - 1)\n  end if"))
        self.none(src)


class Files(unittest.TestCase):
    def test_bad_termination_reports_spin_ping_pong_and_not_fib(self):
        _, diags, ex = zehn.analyze(read(ERR, "bad_termination.zehn"))
        found = [d for d in diags if d["code"] == "E0311"]
        self.assertEqual([c["fn"] for d in found for c in d["cycle"]], ["spin", "ping", "pong"])
        self.assertEqual([d["location"]["fn"] for d in found], ["spin", "ping"])
        self.assertNotIn("fib", json.dumps(found))
        self.assertEqual({d["code"] for d in diags}, {"E0311"})
        self.assertEqual(ex, [], "examples must not run")

    def test_bad_recursion_file_flags_only_total(self):
        _, diags, ex = zehn.analyze(read(ERR, "bad_recursion.zehn"))
        found = [d for d in diags if d["code"] == "E0311"]
        self.assertEqual([d["location"]["fn"] for d in found], ["total"])
        self.assertEqual(ex, [])

    def test_runtime_fixture_is_static_clean_and_still_never_terminates(self):
        _, diags, ex = zehn.analyze(read(ERR, "bad_termination_runtime.zehn"))
        self.assertEqual([d for d in diags if d["severity"] == "error"], [])
        self.assertEqual(sorted(x["diag"]["code"] for x in ex if x["status"] == "fail"),
                         ["E0801", "E0802", "E0802", "E0802"])

    def test_catalog_entry(self):
        meta = json.loads(read(CATALOG, "meta.json"))
        self.assertEqual(sorted(meta), ["dialect", "note", "strict"])
        strict = meta["strict"]
        _, broken, _ = zehn.analyze(read(CATALOG, "broken.zehn"), strict, dialect=meta["dialect"])
        self.assertIn("E0311", [d["code"] for d in broken])
        _, fixed, _ = zehn.analyze(read(CATALOG, "fixed.zehn"), strict, dialect=meta["dialect"])
        self.assertEqual([d for d in fixed if d["severity"] == "error"], [])

    def test_explain_text_is_registered(self):
        self.assertIn("E0311", errors.EXPLAIN)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py"), "explain", "E0311"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Unconditional recursion", r.stdout)

    def test_run_refuses_what_check_refuses(self):
        path = os.path.join(ERR, "bad_termination.zehn")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py"), "run", path, "fib", "[10]"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("E0311", r.stdout + r.stderr)

    def test_pass_is_registered_at_order_400(self):
        self.assertIn((400, "recursion"), [(o, n) for o, n, _ in passes.PASSES])


# ---------------------------------------------------------------------------------------------
# Soundness: whatever is flagged must really never return.
# ---------------------------------------------------------------------------------------------

def _shapes(x):
    """Bodies (for a function returning Result<Int, Text>) that call function `x` somewhere."""
    return [
        "  return %s(n + 1)" % x,                                                       # direct
        "  return %s(n)" % x,
        "  let a = %s(n)?\n  return ok(a + 1)" % x,                                      # call, then ?
        "  let a = n + 1\n  return %s(a)" % x,
        "  return g2(n, %s(n)?)" % x,                                                   # argument
        "  if %s(n) == ok(1) then\n    return ok(1)\n  else\n    return ok(2)\n  end if" % x,
        "  match %s(n) do\n    case ok(v) =>\n      return ok(v)\n    case _ =>\n      return ok(0)\n"
        "  end match" % x,
        "  if n < 0 then\n    return %s(n)\n  else\n    return ok(n)\n  end if" % x,       # under if
        "  if n > 0 then\n    return ok(n)\n  else\n    return %s(n + 1)\n  end if" % x,
        "  match n do\n    case 0 =>\n      return %s(n + 1)\n    case _ =>\n      return ok(n)\n"
        "  end match" % x,
        "  if n < 0 and %s(n) == ok(1) then\n    return ok(1)\n  else\n    return ok(2)\n  end if" % x,
        "  if n >= 0 or %s(n) == ok(1) then\n    return ok(1)\n  else\n    return ok(2)\n  end if" % x,
        "  return ok(n)\n  return %s(n)" % x,                                           # after return
        "  let c = chk(n)?\n  return %s(c)" % x,                                         # after ?
        "  return g2(chk(n)?, %s(n)?)" % x,
        "  if n < 0 then\n    return ok(0)\n  end if\n  return %s(n)" % x,               # after an if that returns
        "  return ok(list.len(list.map([n], %s)))" % x,                                 # as a value
    ]


def _base():
    return ["  return ok(n)", "  return ok(n + 1)"]


def generate(rng):
    count = rng.choice([1, 1, 2, 3])
    names = ["f%d" % i for i in range(count)]
    fns = []
    for name in names:
        if rng.random() < 0.15:
            body = rng.choice(_base())
        else:
            body = rng.choice(_shapes(rng.choice(names)))
        fns.append(rfn(name, body))
    return names, program(*fns, prelude=CHK)


class Soundness(unittest.TestCase):
    SEED = 20260311
    PROGRAMS = 400
    INPUTS = (-1, 0, 2)

    def test_flagged_programs_never_return(self):
        rng = random.Random(self.SEED)
        total = flagged = 0
        for _ in range(self.PROGRAMS):
            names, src = generate(rng)
            self.assertEqual([d for d in static_errors(src) if d["code"] != "E0311"], [], src)
            total += 1
            diags = e0311(src)
            if not diags:
                continue
            flagged += 1
            prog = zehn.parse(src)
            for d in diags:
                for step in d["cycle"]:
                    for n in self.INPUTS:
                        it = zehn.Interp(prog, fuel=2_000, max_depth=40)
                        try:
                            got = it.invoke(prog.funcs[step["fn"]], [n])
                        except zehn.ZehnError as z:
                            self.assertIn(z.diag["code"], ("E0801", "E0802"),
                                          "%s(%d)\n%s" % (step["fn"], n, src))
                        else:
                            self.fail("flagged %s(%d) returned %r\n%s" % (step["fn"], n, got, src))
        self.assertGreaterEqual(total, 300)
        self.assertGreaterEqual(flagged, 20)

    def test_generator_is_deterministic(self):
        a = [generate(random.Random(self.SEED))[1] for _ in range(3)]
        self.assertEqual(a[0], a[1])

    def test_generator_covers_both_outcomes(self):
        """A program that terminates somewhere must never be flagged (the contract), and the
        generator must contain such programs, or the test above would pass trivially."""
        rng = random.Random(self.SEED)
        terminating = 0
        for _ in range(self.PROGRAMS):
            names, src = generate(rng)
            prog = zehn.parse(src)
            if e0311(src):
                continue
            for n in self.INPUTS:
                it = zehn.Interp(prog, fuel=2_000, max_depth=40)
                try:
                    it.invoke(prog.funcs[names[0]], [n])
                    terminating += 1
                    break
                except zehn.ZehnError:
                    pass
        self.assertGreater(terminating, 50)


if __name__ == "__main__":
    unittest.main()
