"""Zehn test-suite.  Run:  python3 -m unittest discover -s tests -v"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import zehn  # noqa: E402

EX = os.path.join(ROOT, "examples")
ERR = os.path.join(ROOT, "errors")


def read(*p):
    with open(os.path.join(*p), encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def codes(src, strict=False):
    _, diags, ex = zehn.analyze(src, strict)
    return sorted({d["code"] for d in diags} | {x["diag"]["code"] for x in ex if x["status"] == "fail"})


def cli(*args):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py")] + list(args),
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class GoodPrograms(unittest.TestCase):
    def test_examples_pass_cleanly(self):
        for name in sorted(os.listdir(EX)):
            src = read(EX, name)
            prog, diags, ex = zehn.analyze(src, strict=False)
            errs = [d for d in diags if d["severity"] == "error"]
            self.assertEqual(errs, [], name)
            self.assertTrue(all(x["status"] == "pass" for x in ex), name)
            self.assertNotIn("W0301", [d["code"] for d in diags], name + " must be canonical")


class BadPrograms(unittest.TestCase):
    def test_bad_runtime(self):
        self.assertEqual(codes(read(ERR, "bad_runtime.zehn")), ["E0401", "E0502"])

    def test_bad_static(self):
        got = codes(read(ERR, "bad_static.zehn"))
        for c in ("E0301", "E0302", "E0304", "E0305", "E0601"):
            self.assertIn(c, got)

    def test_bad_types(self):
        got = codes(read(ERR, "bad_types.zehn"))
        for c in ("E0303", "E0306", "E0308", "E0309"):
            self.assertIn(c, got)

    def test_type_errors_have_hints_and_types(self):
        _, diags, _ = zehn.analyze(read(ERR, "bad_types.zehn"))
        first = next(d for d in diags if d["code"] == "E0306" and d["location"]["fn"] == "label")
        self.assertEqual((first["expected"], first["found"]), ("Text", "Int"))
        self.assertIn("int.to_text", first["fix_hint"])


class TypeChecker(unittest.TestCase):
    def check(self, body, ret="Int", extra=""):
        src = "%sfn f(n: Int) -> %s\n  example f(1) == f(1)\ndo\n%s\nend fn\n" % (extra, ret, body)
        return codes(src)

    def test_accepts_inferred_lists_and_options(self):
        self.assertNotIn("E0306", self.check("  let xs = []\n  return list.len(list.append(xs, 1))"))
        self.assertNotIn("E0306", self.check("  let o = none\n  return option.unwrap_or(o, 3)"))

    def test_rejects_mixed_list(self):
        self.assertIn("E0306", self.check('  let xs = [1, "a"]\n  return 1'))

    def test_empty_map_takes_type_from_annotation(self):
        self.assertEqual(self.check("  let m: Map<Text, Int> = map.empty()\n  return map.len(map.set(m, \"a\", n))"), [])

    def test_wrong_map_value_type(self):
        self.assertIn("E0306", self.check("  let m: Map<Text, Int> = map.empty()\n  return map.len(map.set(m, \"a\", \"b\"))"))

    def test_option_vs_value(self):
        self.assertIn("E0306", self.check("  return list.get([1], 0)"))

    def test_try_error_types_must_match(self):
        extra = "type A = A1\ntype B = B1\nfn g() -> Result<Int, A>\n  example g() == ok(1)\ndo\n  return ok(1)\nend fn\n\n"
        self.assertIn("E0306", self.check("  let v = g()?\n  return ok(v)", "Result<Int, B>", extra))
        self.assertNotIn("E0306", self.check("  let v = g()?\n  return ok(v)", "Result<Int, A>", extra))

    def test_match_pattern_types(self):
        self.assertIn("E0306", self.check('  match n do\n    case "x" =>\n      return 1\n    case _ =>\n      return 2\n  end match'))

    def test_unknown_type_name(self):
        self.assertIn("E0302", codes("fn f(a: Strng) -> Int\n  example f(\"a\") == 1\ndo\n  return 1\nend fn\n"))

    def test_generic_arity(self):
        self.assertIn("E0302", codes("fn f(a: List<Int, Int>) -> Int\n  example f([]) == 1\ndo\n  return 1\nend fn\n"))

    def test_all_builtins_have_signatures(self):
        self.assertEqual(set(zehn.BUILTINS), set(zehn.SIGS))
        for sig in zehn.SIGS.values():
            zehn.instantiate(sig)


class Formatter(unittest.TestCase):
    def files(self):
        out = []
        for d in (EX, ERR):
            for n in sorted(os.listdir(d)):
                out.append(read(d, n))
        return out

    def test_idempotent(self):
        for src in self.files():
            once = zehn.format_program(zehn.parse(src))
            self.assertEqual(once, zehn.format_program(zehn.parse(once)))

    def test_preserves_semantics(self):
        for src in self.files():
            a = zehn.analyze(src)
            b = zehn.analyze(zehn.format_program(zehn.parse(src)))
            self.assertEqual(sorted(d["code"] for d in a[1] if d["code"] != "W0301"),
                             sorted(d["code"] for d in b[1] if d["code"] != "W0301"))

    def test_pipe_is_desugared(self):
        src = "fn f(a: Int) -> Int\n  example f(1) == 2\ndo\n  return a |> int.max(2)\nend fn\n"
        self.assertIn("int.max(a, 2)", zehn.format_program(zehn.parse(src)))

    def test_minimal_parentheses(self):
        src = "fn p(a: Int) -> Int\n  example p(1) == 4\ndo\n  return (a * 2) + (a - (1 - a)) - -(a)\nend fn\n"
        out = zehn.format_program(zehn.parse(src))
        self.assertIn("return a * 2 + (a - (1 - a)) - -a", out)
        self.assertEqual(zehn.analyze(src)[2][0]["status"], "pass")

    def test_comments_survive(self):
        src = "-- top\nfn f() -> Int  -- tail\n  example f() == 1\ndo\n  -- in body\n  return 1\nend fn\n"
        out = zehn.format_program(zehn.parse(src))
        for c in ("-- top", "-- tail", "-- in body"):
            self.assertIn(c, out)

    def test_non_canonical_warns_and_strict_errors(self):
        src = read(EX, "shapes.zehn").replace("\n\nfn describe", "\nfn describe")
        self.assertIn("W0301", codes(src))
        self.assertIn("E0203", codes(src, strict=True))


class HashAndPatch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "shapes.zehn")
        write(self.path, read(EX, "shapes.zehn"))

    def refs(self):
        return {r["name"]: r["ref"] for r in zehn.definition_refs(zehn.parse(read(self.path)))}

    def test_hash_is_stable_and_content_based(self):
        a = self.refs()
        self.assertEqual(a, self.refs())
        src = read(self.path).replace("return 0\n  end match\nend fn\n\nfn describe", "return 1\n  end match\nend fn\n\nfn describe", 1)
        b = {r["name"]: r["ref"] for r in zehn.definition_refs(zehn.parse(src))}
        self.assertNotEqual(a["area"], b["area"])
        self.assertEqual(a["describe"], b["describe"])

    def test_comment_change_keeps_hash(self):
        src = "-- hello\n" + read(self.path)
        b = {r["name"]: r["ref"] for r in zehn.definition_refs(zehn.parse(src))}
        self.assertEqual(self.refs(), b)

    def test_replace_roundtrip(self):
        new = os.path.join(self.dir, "new.zehn")
        write(new, 
            'fn first_area(shapes: List<Shape>) -> Option<Int>\n  example first_area([]) == none\ndo\n  return option.map(list.get(shapes, 0), area)\nend fn\n')
        old_ref = self.refs()["first_area"]
        rc, out, err = cli("patch", self.path, "replace", old_ref, "--with", new, "--write")
        self.assertEqual(rc, 0, err)
        self.assertNotEqual(self.refs()["first_area"], old_ref)
        rc, out, err = cli("patch", self.path, "replace", old_ref, "--with", new)
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["code"], "E0701")

    def test_bad_patch_is_not_written(self):
        bad = os.path.join(self.dir, "bad.zehn")
        write(bad, 
            'fn first_area(shapes: List<Shape>) -> Option<Int>\n  example first_area([]) == none\ndo\n  return list.get(shapes, 0)\nend fn\n')
        before = read(self.path)
        rc, _, err = cli("patch", self.path, "replace", self.refs()["first_area"], "--with", bad, "--write")
        self.assertEqual(rc, 1)
        self.assertIn("E0306", err)
        self.assertEqual(before, read(self.path))

    def test_delete_with_dependents_is_refused(self):
        rc, _, err = cli("patch", self.path, "delete", self.refs()["area"], "--write")
        self.assertEqual(rc, 1)
        self.assertIn("E0302", err)

    def test_kind_mismatch(self):
        new = os.path.join(self.dir, "t.zehn")
        write(new, "type Shape = Dot\n")
        rc, out, _ = cli("patch", self.path, "replace", self.refs()["area"], "--with", new)
        self.assertEqual(json.loads(out)["code"], "E0703")


class IntentDrift(unittest.TestCase):
    def test_drift_detected_only_after_lock(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "s.zehn")
        write(p, read(EX, "shapes.zehn"))
        self.assertEqual(cli("lock", p)[0], 0)
        self.assertNotIn("W0201", cli("check", p)[1])
        write(p, read(p).replace("r * r * 3", "r * r * 4").replace("== 12\n  example area(Rect", "== 16\n  example area(Rect", 1))
        self.assertIn("W0201", cli("check", p)[1])
        # changing the intent confirms the new behaviour
        write(p, read(p).replace("π ≈ 3", "π ≈ 4"))
        self.assertNotIn("W0201", cli("check", p)[1])


class Capabilities(unittest.TestCase):
    path = os.path.join(EX, "effects.zehn")

    def test_static_effect_rules(self):
        src = "fn f() -> Unit\n  example f() == f()\ndo\n  return console.print(\"x\")\nend fn\n"
        self.assertIn("E0601", codes(src))
        self.assertIn("E0602", codes("fn f(n: Int) -> Bool\n  uses [console]\n  example console.print(\"x\") == f(1)\ndo\n  return true\nend fn\n"))

    def test_fn_used_as_value_needs_effect(self):
        src = ("fn noisy(n: Int) -> Int\n  uses [console]\ndo\n  let u = console.print(\"x\")\n  return n\nend fn\n\n"
               "fn quiet(xs: List<Int>) -> List<Int>\n  example quiet([]) == []\ndo\n  return list.map(xs, noisy)\nend fn\n")
        self.assertIn("E0601", codes(src))

    def test_host_must_grant(self):
        rc, out, _ = cli("run", self.path, "greet", '["Ali"]')
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["code"], "E0604")
        self.assertEqual(json.loads(out)["blame"], "host")
        rc, out, _ = cli("run", self.path, "greet", '["Ali"]', "--grant", "console")
        self.assertEqual((rc, out), (0, "hello, Ali\nunit\n"))

    def test_time_is_injectable_for_determinism(self):
        rc, out, _ = cli("run", self.path, "stamp", "[]", "--grant", "time.now", "--now", "7")
        self.assertEqual((rc, out.strip()), (0, "7"))

    def test_runtime_guard_against_undeclared_effect(self):
        prog = zehn.parse(read(EX, "effects.zehn"))
        it = zehn.Interp(prog, granted={"console"}, stdout=io.StringIO())
        it.frames.append(set())   # simulate a frame that declared nothing
        with self.assertRaises(zehn.ZehnError) as cm:
            it.need("console", "console.print", 1)
        self.assertEqual(cm.exception.diag["code"], "E0603")


class MapSemantics(unittest.TestCase):
    def run_fn(self, body, ret="Int"):
        src = "fn f() -> %s\n  example f() == f()\ndo\n%s\nend fn\n" % (ret, body)
        prog = zehn.parse(src)
        return zehn.Interp(prog).call_fn(prog.funcs["f"], [])

    def test_insertion_order_and_update_in_place(self):
        out = self.run_fn('  let m = map.set(map.set(map.set(map.empty(), "b", 1), "a", 2), "b", 9)\n  return map.keys(m)', "List<Text>")
        self.assertEqual(out, ["b", "a"])

    def test_equality_ignores_order(self):
        a = zehn.MapV((("x", 1), ("y", 2)))
        b = zehn.MapV((("y", 2), ("x", 1)))
        self.assertTrue(zehn.eq(a, b))
        self.assertFalse(zehn.eq(a, zehn.MapV((("x", 1),))))

    def test_structured_keys(self):
        out = self.run_fn('  let m = map.set(map.empty(), [1, 2], "v")\n  return map.has(m, [1, 2])', "Bool")
        self.assertIs(out, True)

    def test_remove_and_get(self):
        out = self.run_fn('  let m = map.remove(map.set(map.empty(), 1, 2), 1)\n  return map.get(m, 1)', "Option<Int>")
        self.assertEqual(out.name, "none")


class Contracts(unittest.TestCase):
    def test_division_by_zero_blames_caller(self):
        src = "fn d(a: Int, b: Int) -> Int\n  example d(4, 2) == 2\ndo\n  return a / b\nend fn\n"
        prog = zehn.parse(src)
        with self.assertRaises(zehn.ZehnError) as cm:
            zehn.Interp(prog).call_fn(prog.funcs["d"], [1, 0])
        self.assertEqual(cm.exception.diag["code"], "E0505")

    def test_shadowing_forbidden(self):
        src = "fn f(n: Int) -> Int\n  example f(1) == 1\ndo\n  let n = 2\n  return n\nend fn\n"
        self.assertIn("E0307", codes(src))

    def test_json_diagnostics_shape(self):
        rc, out, _ = cli("check", os.path.join(ERR, "bad_runtime.zehn"), "--json")
        data = json.loads(out)
        self.assertFalse(data["ok"])
        self.assertTrue(all(r["ref"].startswith("fn#") for r in data["definitions"]))


def fn_src(body, ret="Int", params="n: Int", ex="f(1) == 1"):
    """One function `f` whose body is the given (already indented) text."""
    return "fn f(%s) -> %s\n  example %s\ndo\n%s\nend fn\n" % (params, ret, ex, body)


class ReturnPaths(unittest.TestCase):
    """SPEC 5: every path through a body must end in `return` (E0310)."""

    def falls(self, src):
        _, diags, _ = zehn.analyze(src)
        return [d for d in diags if d["code"] == "E0310"]

    def test_if_without_else(self):
        d = self.falls(fn_src("  if n > 0 then\n    return 1\n  end if"))
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["location"]["fn"], "f")
        self.assertIn("no `else`", d[0]["falls_through"][0]["where"])

    def test_if_else_both_return_is_fine(self):
        self.assertEqual(self.falls(fn_src(
            "  if n > 0 then\n    return 1\n  else\n    return 2\n  end if")), [])

    def test_else_branch_falls_off(self):
        d = self.falls(fn_src(
            "  if n > 0 then\n    return 1\n  else\n    let x = 2\n  end if"))
        self.assertIn("`else` branch", d[0]["falls_through"][0]["where"])

    def test_every_gap_is_listed(self):
        src = ("type S = A | B | C\n\nfn f(s: S) -> Int\n  example f(A) == 1\ndo\n  match s do\n"
               "    case A =>\n      let x = 1\n    case B =>\n      return 2\n    case C =>\n"
               "      let y = 3\n  end match\nend fn\n")
        d = self.falls(src)
        self.assertEqual(len(d), 1)
        self.assertEqual(len(d[0]["falls_through"]), 2)
        self.assertTrue(all("falls off" in g["where"] for g in d[0]["falls_through"]))

    def test_match_all_cases_return_is_fine(self):
        src = ("type S = A | B\n\nfn f(s: S) -> Int\n  example f(A) == 1\ndo\n  match s do\n"
               "    case A =>\n      return 1\n    case B =>\n      return 2\n  end match\nend fn\n")
        self.assertEqual(self.falls(src), [])

    def test_nested_if_inside_match(self):
        src = ("type S = A | B\n\nfn f(s: S, n: Int) -> Int\n  example f(A, 1) == 1\ndo\n  match s do\n"
               "    case A =>\n      if n > 0 then\n        return 1\n      end if\n"
               "    case B =>\n      return 2\n  end match\nend fn\n")
        self.assertEqual(len(self.falls(src)), 1)

    def test_try_does_not_count_as_return(self):
        src = ("fn f(t: Text) -> Result<Int, Text>\n  example f(\"a\") == ok(1)\ndo\n"
               "  let x = ok(1)?\nend fn\n")
        self.assertEqual(len(self.falls(src)), 1)

    def test_empty_body_is_an_error(self):
        self.assertEqual(len(self.falls("fn f() -> Int\n  example f() == 1\ndo\nend fn\n")), 1)

    def test_fall_through_in_middle_is_fine_when_end_returns(self):
        self.assertEqual(self.falls(fn_src(
            "  if n > 0 then\n    let x = 1\n  end if\n  return 3")), [])

    def test_unreachable_statement_is_a_warning_not_an_error(self):
        _, diags, ex = zehn.analyze(fn_src("  return n\n  let dead = 1"))
        self.assertEqual([d["code"] for d in diags if d["severity"] == "error"], [])
        w = [d for d in diags if d["code"] == "W0102"]
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0]["location"]["line"], 5)

    def test_unreachable_after_exhaustive_if(self):
        src = fn_src("  if n > 0 then\n    return 1\n  else\n    return 2\n  end if\n  return 3")
        self.assertIn("W0102", codes(src))

    def test_error_program_does_not_run_its_examples(self):
        # E0310 must stop the example run: the example would otherwise hit the runtime E0503.
        _, diags, ex = zehn.analyze(fn_src("  if n > 5 then\n    return 1\n  end if"))
        self.assertEqual(ex, [])

    def test_run_refuses_what_check_refuses(self):
        path = os.path.join(ERR, "bad_return.zehn")
        rc, out, _ = cli("run", path, "sign", "[-3]")
        self.assertEqual(rc, 1)
        self.assertIn("E0310", out)
        self.assertNotIn("E0503", out)

    def test_bad_return_file(self):
        got = codes(read(ERR, "bad_return.zehn"))
        self.assertIn("E0310", got)
        self.assertIn("W0102", got)

    def test_runtime_guard_remains_as_defence_in_depth(self):
        prog = zehn.parse(fn_src("  if n > 5 then\n    return 1\n  end if"))
        with self.assertRaises(zehn.ZehnError) as cm:
            zehn.Interp(prog).call_fn(prog.funcs["f"], [0])     # bypasses the static check
        self.assertEqual(cm.exception.diag["code"], "E0503")


class ResourceLimits(unittest.TestCase):
    """SPEC 13: fuel and call depth turn non-termination into diagnostics."""

    SPIN = fn_src("  return f(n + 1)", ex="f(1) == 1")
    # same endless recursion, but conditional, so the static E0311 lets it reach run time
    SPIN_RT = fn_src("  if n < 0 then\n    return 0\n  else\n    return f(n + 1)\n  end if", ex="f(1) == 1")

    def call(self, src, fname, args, **kw):
        prog = zehn.parse(src)
        return zehn.Interp(prog, **kw).invoke(prog.funcs[fname], args)

    def err(self, src, fname, args, **kw):
        with self.assertRaises(zehn.ZehnError) as cm:
            self.call(src, fname, args, **kw)
        return cm.exception.diag

    def test_unbounded_recursion_is_e0802(self):
        d = self.err(self.SPIN, "f", [0], max_depth=100)
        self.assertEqual(d["code"], "E0802")
        self.assertEqual(d["depth_limit"], 100)
        self.assertEqual(d["call_stack"]["depth"], 100)
        self.assertEqual(d["call_stack"]["most_frequent"], "f")
        self.assertEqual(d["blame"], "callee")
        self.assertIn("base case", d["fix_hint"])

    def test_default_depth_is_10000(self):
        self.assertEqual(zehn.DEFAULT_DEPTH, 10_000)
        _, diags, ex = zehn.analyze(self.SPIN_RT)
        self.assertEqual(ex[0]["diag"]["depth_limit"], 10_000)

    def test_mutual_recursion_is_summarised_as_a_cycle(self):
        src = ("fn a(n: Int) -> Int\n  example a(1) == 1\ndo\n  return b(n)\nend fn\n\n"
               "fn b(n: Int) -> Int\n  example b(1) == 1\ndo\n  return a(n)\nend fn\n")
        d = self.err(src, "a", [0], max_depth=60)
        names = [g["fn"] for g in d["call_stack"]["innermost"]]
        self.assertEqual(set(names), {"a", "b"})
        self.assertEqual(d["call_stack"]["most_frequent_count"], 30)

    def test_exponential_work_exhausts_fuel_at_shallow_depth(self):
        src = fn_src("  if n < 2 then\n    return n\n  else\n    return f(n - 1) + f(n - 2)\n  end if")
        d = self.err(src, "f", [40], fuel=100_000)
        self.assertEqual(d["code"], "E0801")
        self.assertEqual(d["fuel_limit"], 100_000)
        self.assertLess(d["call_stack"]["depth"], 50)

    def test_enough_fuel_lets_it_finish(self):
        src = fn_src("  if n < 2 then\n    return n\n  else\n    return f(n - 1) + f(n - 2)\n  end if")
        self.assertEqual(self.call(src, "f", [15], fuel=1_000_000), 610)

    def test_fuel_is_deterministic(self):
        src = fn_src("  if n < 2 then\n    return n\n  else\n    return f(n - 1) + f(n - 2)\n  end if")
        used = []
        for _ in range(2):
            prog = zehn.parse(src)
            it = zehn.Interp(prog)
            it.invoke(prog.funcs["f"], [12])
            used.append(it.used)
        self.assertEqual(used[0], used[1])
        self.assertGreater(used[0], 100)

    def test_diagnostics_are_identical_across_runs(self):
        a = zehn.analyze(self.SPIN_RT)[2][0]["diag"]
        b = zehn.analyze(self.SPIN_RT)[2][0]["diag"]
        self.assertEqual(a, b)

    def test_each_example_gets_a_fresh_budget(self):
        src = ("fn f(n: Int) -> Int\n  example f(100) == 100\n  example f(100) == 100\n"
               "  example f(100) == 100\ndo\n  if n == 0 then\n    return 0\n  else\n"
               "    return 1 + f(n - 1)\n  end if\nend fn\n")
        # one example costs ~1700 steps; three of them share nothing
        _, diags, ex = zehn.analyze(src, fuel=2_500)
        self.assertTrue(all(x["status"] == "pass" for x in ex), ex)

    def test_contracts_are_metered_too(self):
        src = ("fn loop(n: Int) -> Int\n  example loop(1) == 1\ndo\n  if n < 0 then\n    return 0\n  else\n    return loop(n)\n  end if\nend fn\n\n"
               "fn g(n: Int) -> Int\n  requires loop(n) == 0\n  example g(1) == 1\ndo\n  return n\nend fn\n")
        _, diags, ex = zehn.analyze(src, max_depth=50)
        self.assertEqual({x["diag"]["code"] for x in ex if x["status"] == "fail"}, {"E0802"})

    def test_deep_but_legitimate_recursion_passes(self):
        src = ("fn f(n: Int) -> Int\n  example f(5000) == 5000\ndo\n  if n == 0 then\n    return 0\n"
               "  else\n    return 1 + f(n - 1)\n  end if\nend fn\n")
        _, diags, ex = zehn.analyze(src)
        self.assertEqual([x["status"] for x in ex], ["pass"])

    def test_big_integer_growth_is_stopped_quickly(self):
        import time
        src = ("fn f(x: Int, n: Int) -> Int\n  example f(1, 0) == 1\ndo\n  if n == 0 then\n"
               "    return x\n  else\n    return f(x * x, n - 1)\n  end if\nend fn\n")
        t = time.time()
        d = self.err(src, "f", [3, 40])
        self.assertEqual(d["code"], "E0801")
        self.assertLess(time.time() - t, 3.0)

    def test_big_integers_below_the_budget_are_exact(self):
        src = ("fn f(n: Int) -> Int\n  example f(0) == 1\ndo\n  if n == 0 then\n    return 1\n"
               "  else\n    return n * f(n - 1)\n  end if\nend fn\n")
        out = self.call(src, "f", [2000])          # 5736 digits: past Python's default str limit
        self.assertEqual(len(str(out)), 5736)
        self.assertEqual(zehn.show(out)[:6], "331627")

    def test_list_operations_are_charged_by_size(self):
        src = ("fn f(n: Int) -> Int\n  example f(0) == 0\ndo\n  let xs = list.map([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], g)\n"
               "  return list.sum(xs)\nend fn\n\nfn g(x: Int) -> Int\n  example g(1) == 1\ndo\n  return x\nend fn\n")
        prog = zehn.parse(src)
        it = zehn.Interp(prog)
        it.invoke(prog.funcs["f"], [0])
        small = it.used
        src2 = src.replace("[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", "[" + ", ".join(["1"] * 40) + "]")
        prog2 = zehn.parse(src2)
        it2 = zehn.Interp(prog2)
        it2.invoke(prog2.funcs["f"], [0])
        self.assertGreater(it2.used, small + 30 * 3)

    def test_host_stack_backstop_never_leaks_a_traceback(self):
        src = "fn f() -> Int\n  example f() == 1\ndo\n  return " + "(" * 3000 + "1" + ")" * 3000 + "\nend fn\n"
        _, diags, ex = zehn.analyze(src)
        self.assertIn("E0204", [d["code"] for d in diags])

    def test_bad_termination_file(self):
        _, diags, ex = zehn.analyze(read(ERR, "bad_termination_runtime.zehn"))
        got = [x["diag"]["code"] for x in ex if x["status"] == "fail"]
        self.assertEqual(sorted(got), ["E0801", "E0802", "E0802", "E0802"])

    def test_recursion_example_is_clean_and_strict(self):
        rc, out, _ = cli("check", os.path.join(EX, "recursion.zehn"), "--strict")
        self.assertEqual(rc, 0, out)


class LimitCLI(unittest.TestCase):
    def test_run_reports_fuel_as_json_not_a_traceback(self):
        rc, out, err = cli("run", os.path.join(ERR, "bad_termination_runtime.zehn"), "fib", "[40]")
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["code"], "E0801")
        self.assertNotIn("Traceback", err)

    def test_run_infinite_recursion_exits_cleanly(self):
        rc, out, err = cli("run", os.path.join(ERR, "bad_termination_runtime.zehn"), "spin", "[0]")
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["code"], "E0802")
        self.assertNotIn("Traceback", err)

    def test_fuel_flag(self):
        path = os.path.join(EX, "recursion.zehn")
        rc, out, _ = cli("run", path, "sum_to", "[500]")
        self.assertEqual((rc, out.strip()), (0, "125250"))
        rc, out, _ = cli("run", path, "sum_to", "[500]", "--fuel", "300")
        self.assertEqual(json.loads(out)["code"], "E0801")

    def test_max_depth_flag(self):
        path = os.path.join(EX, "recursion.zehn")
        rc, out, _ = cli("run", path, "sum_to", "[500]", "--max-depth", "100")
        self.assertEqual(json.loads(out)["code"], "E0802")
        rc, out, _ = cli("run", path, "sum_to", "[500]", "--max-depth", "600")
        self.assertEqual(out.strip(), "125250")

    def test_check_accepts_limit_flags(self):
        rc, out, _ = cli("check", os.path.join(EX, "recursion.zehn"), "--fuel", "500", "--json")
        data = json.loads(out)
        self.assertFalse(data["ok"])
        self.assertEqual({r["diag"]["code"] for r in data["examples"]["results"] if r["status"] == "fail"},
                         {"E0801"})

    def test_bad_option_value_is_a_usage_error(self):
        rc, out, _ = cli("run", os.path.join(EX, "recursion.zehn"), "gcd", "[4, 6]", "--fuel", "lots")
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["code"], "E0001")

    def test_explain_knows_the_new_codes(self):
        for code in ("E0310", "E0801", "E0802", "W0102", "E0204"):
            rc, out, _ = cli("explain", code)
            self.assertNotIn("unknown code", out, code)


if __name__ == "__main__":
    unittest.main()
