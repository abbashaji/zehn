"""TASK 07: tuple expressions and tuple patterns (E0313-E0318, E0301 for tuple patterns)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import zehn  # noqa: E402
from zehnlib.errors import EXPLAIN  # noqa: E402
from zehnlib.fmt import format_program  # noqa: E402
from zehnlib.values import Tup, eq, show  # noqa: E402

NEW_CODES = ["E0313", "E0314", "E0315", "E0316", "E0317", "E0318"]


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def fn(body, params="p: (Int, Int)", ret="Int", example="f((1, 2)) == 3", extra=""):
    return ("%sfn f(%s) -> %s\n  example %s\ndo\n%s\nend fn\n"
            % (extra, params, ret, example, "\n".join("  " + ln for ln in body.split("\n"))))


def codes(src, strict=False):
    _, diags, ex = zehn.analyze(src, strict=strict)
    return sorted({d["code"] for d in diags if d["severity"] == "error"}
                  | {x["diag"]["code"] for x in ex if x["status"] == "fail"})


def diags_of(src, code):
    _, diags, _ = zehn.analyze(src)
    return [d for d in diags if d["code"] == code]


def value(expr_src, params="", args=()):
    """Evaluate `expr_src` as the body of a function with no declared example."""
    prog = zehn.parse("fn f(%s) -> Int\ndo\n  return 0\nend fn\n" % params)
    it = zehn.Interp(prog)
    it.fresh_budget()
    from zehnlib.parser import Parser
    from zehnlib.lexer import tokenize
    e = Parser(tokenize(expr_src), expr_src).expr()
    return it.eval(e, dict(args)), it.used


def cli(*args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py")] + list(args), cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return p.returncode, p.stdout


class Construction(unittest.TestCase):
    def test_tuple_values(self):
        v, _ = value('(1, "a", true)')
        self.assertEqual(v, Tup((1, "a", True)))
        self.assertIsInstance(v, Tup)

    def test_nested(self):
        v, _ = value('(1, ("a", (true, 2)))')
        self.assertEqual(show(v), '(1, ("a", (true, 2)))')

    def test_parenthesised_expression_is_not_a_tuple(self):
        v, _ = value("(1 + 2) * 3")
        self.assertEqual(v, 9)
        v, _ = value("((4))")
        self.assertEqual(v, 4)

    def test_elements_are_arbitrary_expressions(self):
        v, _ = value("(a + 1, [a, a], f2)", "a: Int", {"a": 5, "f2": "x"}.items())
        self.assertEqual(show(v), '(6, [5, 5], "x")')

    def test_pipeline_into_a_tuple_element_and_from_a_tuple(self):
        src = ('fn swap(p: (Int, Text)) -> (Text, Int)\n  example swap((1, "a")) == ("a", 1)\n'
               'do\n  match p do\n    case (n, t) =>\n      return (t, n)\n  end match\nend fn\n\n'
               'fn g(n: Int) -> (Text, Int)\n  example g(2) == ("b", 2)\n'
               'do\n  return (n, "b") |> swap\nend fn\n')
        self.assertEqual(codes(src), [])

    def test_tuple_in_signature_let_return_and_variant(self):
        src = ('type Move = Step((Int, Int)) | Stay\n\n'
               'fn f(m: Move) -> (Int, Int)\n  example f(Step((1, 2))) == (1, 2)\n  example f(Stay) == (0, 0)\n'
               'do\n  let zero: (Int, Int) = (0, 0)\n  match m do\n    case Step(d) =>\n      return d\n'
               '    case Stay =>\n      return zero\n  end match\nend fn\n')
        self.assertEqual(codes(src), [])


class Equality(unittest.TestCase):
    def test_structural_equality(self):
        self.assertTrue(eq(Tup((1, "a")), Tup((1, "a"))))
        self.assertFalse(eq(Tup((1, "a")), Tup((1, "b"))))
        self.assertFalse(eq(Tup((1, 2)), Tup((1, 2, 3))))

    def test_bool_is_not_int_inside_a_tuple(self):
        self.assertFalse(eq(Tup((True, 1)), Tup((1, True))))
        self.assertFalse(eq(Tup((1,)), Tup((True,))))

    def test_deep_equality_and_not_equal_operator(self):
        v, _ = value('((1, [2, 3]), "x") == ((1, [2, 3]), "x")')
        self.assertIs(v, True)
        v, _ = value('(1, 2) != (1, 3)')
        self.assertIs(v, True)

    def test_tuples_are_not_lists(self):
        self.assertFalse(eq(Tup((1, 2)), [1, 2]))
        self.assertEqual(codes(fn("return [1, 2] == (1, 2)", ret="Bool", example="f((1, 2)) == true")),
                         ["E0306"])

    def test_list_contains_uses_structural_equality(self):
        src = fn("return list.contains([(1, 2), (3, 4)], p)", ret="Bool",
                 example="f((3, 4)) == true")
        self.assertEqual(codes(src), [])


class Patterns(unittest.TestCase):
    SRC = ('fn f(a: Int, b: Int) -> Text\n  example f(0, 0) == "origin"\n  example f(0, 5) == "on y"\n'
           '  example f(5, 0) == "on x"\n  example f(1, 1) == "elsewhere"\ndo\n'
           '  match (a, b) do\n    case (0, 0) =>\n      return "origin"\n    case (0, _) =>\n'
           '      return "on y"\n    case (_, 0) =>\n      return "on x"\n    case (_, _) =>\n'
           '      return "elsewhere"\n  end match\nend fn\n')

    def test_literals_and_wildcards(self):
        self.assertEqual(codes(self.SRC), [])

    def test_names_bind(self):
        src = fn("match p do\n  case (a, b) =>\n    return a * 10 + b\nend match", example="f((4, 2)) == 42")
        self.assertEqual(codes(src), [])

    def test_text_and_bool_literals_and_nested_patterns(self):
        src = ('fn f(p: (Text, (Bool, Int))) -> Int\n  example f(("a", (true, 1))) == 1\n'
               '  example f(("b", (true, 7))) == 7\n  example f(("a", (false, 9))) == 0\n'
               'do\n  match p do\n    case ("a", (true, n)) =>\n      return n\n'
               '    case (_, (true, n)) =>\n      return n\n    case (_, (false, _)) =>\n'
               '      return 0\n  end match\nend fn\n')
        self.assertEqual(codes(src), [])

    def test_first_matching_case_wins(self):
        src = ('fn f(p: (Int, Int)) -> Int\n  example f((0, 9)) == 1\n  example f((3, 9)) == 2\n'
               'do\n  match p do\n    case (0, _) =>\n      return 1\n    case _ =>\n'
               '      return 2\n  end match\nend fn\n')
        self.assertEqual(codes(src), [])

    def test_tuple_inside_a_variant_pattern(self):
        src = ('fn f(o: Option<(Int, Int)>) -> Int\n  example f(some((1, 2))) == 3\n  example f(none) == 0\n'
               'do\n  match o do\n    case some((a, b)) =>\n      return a + b\n    case none =>\n'
               '      return 0\n  end match\nend fn\n')
        self.assertEqual(codes(src), [])

    def test_duplicate_name_in_one_pattern_is_shadowing(self):
        src = fn("match p do\n  case (a, a) =>\n    return a\nend match", example="f((1, 1)) == 1")
        self.assertEqual(codes(src), ["E0307"])

    def test_runtime_mismatch_is_not_a_match(self):
        prog = zehn.parse(self.SRC)
        it = zehn.Interp(prog)
        pat = prog.funcs["f"].body[0].cases[0][0]
        self.assertEqual(it.pmatch(pat, Tup((0, 0))), {})
        self.assertIsNone(it.pmatch(pat, Tup((0, 1))))
        self.assertIsNone(it.pmatch(pat, Tup((0, 0, 0))))
        self.assertIsNone(it.pmatch(pat, [0, 0]))


class Exhaustiveness(unittest.TestCase):
    COLOR = "type Color = Red | Green | Blue\n\n"

    def f(self, cases, params="c: Color, flag: Bool", subject="(c, flag)"):
        body = "match %s do\n%s\nend match" % (subject, "\n".join(
            "  case %s =>\n    return %d" % (p, i) for i, p in enumerate(cases)))
        return self.COLOR + fn(body, params=params, example="f(Red, true) == 0")

    def msg(self, src):
        return [d["message"] for d in diags_of(src, "E0301")]

    def test_complete_without_wildcard(self):
        src = self.f(["(Red, _)", "(Green, true)", "(Green, false)", "(Blue, _)"])
        self.assertEqual(codes(src), [])

    def test_missing_case_is_reported_with_a_witness(self):
        src = self.f(["(Red, true)", "(Green, _)", "(Blue, false)"])
        self.assertEqual(codes(src), ["E0301"])
        self.assertEqual(self.msg(src), ["non-exhaustive match: missing (Red, false)"])

    def test_missing_constructor(self):
        src = self.f(["(Red, _)", "(Green, _)"])
        self.assertEqual(self.msg(src), ["non-exhaustive match: missing (Blue, _)"])

    def test_wildcard_or_name_covers_everything(self):
        self.assertEqual(codes(self.f(["(Red, _)", "_"])), [])
        self.assertEqual(codes(self.f(["(Red, _)", "rest"])), [])
        self.assertEqual(codes(self.f(["(_, _)"])), [])
        self.assertEqual(codes(self.f(["(a, b)"])), [])

    def test_int_literals_never_cover(self):
        src = fn("match p do\n  case (0, 0) =>\n    return 1\n  case (1, _) =>\n    return 2\nend match")
        self.assertEqual(self.msg(src), ["non-exhaustive match: missing (_, _)"])

    def test_option_pairs(self):
        full = ('fn f(a: Option<Int>, b: Option<Int>) -> Int\n  example f(none, none) == 0\ndo\n'
                '  match (a, b) do\n    case (some(x), some(y)) =>\n      return x + y\n'
                '    case (some(x), none) =>\n      return x\n    case (none, some(y)) =>\n'
                '      return y\n    case (none, none) =>\n      return 0\n  end match\nend fn\n')
        self.assertEqual(codes(full), [])
        short = full.replace("    case (none, some(y)) =>\n      return y\n", "")
        self.assertEqual(self.msg(short), ["non-exhaustive match: missing (none, some(_))"])

    def test_result_pairs(self):
        src = ('fn f(a: Result<Int, Text>, b: Bool) -> Int\n  example f(ok(1), true) == 1\ndo\n'
               '  match (a, b) do\n    case (ok(x), true) =>\n      return x\n    case (err(_), _) =>\n'
               '      return 0\n  end match\nend fn\n')
        self.assertEqual(self.msg(src), ["non-exhaustive match: missing (ok(_), false)"])

    def test_bool_pair(self):
        src = ('fn f(a: Bool, b: Bool) -> Int\n  example f(true, true) == 1\ndo\n'
               '  match (a, b) do\n    case (true, true) =>\n      return 1\n    case (true, false) =>\n'
               '      return 2\n    case (false, _) =>\n      return 3\n  end match\nend fn\n')
        self.assertEqual(codes(src), [])
        self.assertEqual(self.msg(src.replace("    case (false, _) =>\n      return 3\n", "")),
                         ["non-exhaustive match: missing (false, _)"])

    def test_nested_tuple(self):
        src = fn("match p do\n  case ((a, true), c) =>\n    return a\nend match",
                 params="p: ((Int, Bool), Int)", example="f(((1, true), 2)) == 1")
        self.assertEqual(self.msg(src), ["non-exhaustive match: missing ((_, false), _)"])

    def test_a_tuple_of_names_inside_a_variant_is_irrefutable(self):
        src = ('fn f(o: Option<(Int, Int)>) -> Int\n  example f(none) == 0\ndo\n  match o do\n'
               '    case some((a, b)) =>\n      return a\n  end match\nend fn\n')
        self.assertEqual(self.msg(src), ["non-exhaustive match: missing none"])

    def test_inconsistent_patterns_leave_the_report_to_the_type_checker(self):
        src = fn("match p do\n  case (a, b) =>\n    return a\n  case (a, b, c) =>\n    return a\nend match")
        got = codes(src)
        self.assertNotIn("E0301", got)
        self.assertIn("E0313", got)


class TypeErrors(unittest.TestCase):
    def test_pattern_arity_e0313(self):
        src = fn("match p do\n  case (a, b, c) =>\n    return a\nend match")
        d = diags_of(src, "E0313")
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["expected"], "(Int, Int)")
        self.assertEqual(codes(src), ["E0313"])

    def test_pattern_on_a_non_tuple_e0315(self):
        src = fn("match n do\n  case (a, b) =>\n    return a\nend match", params="n: Int", example="f(1) == 1")
        self.assertEqual(codes(src), ["E0315"])
        self.assertEqual(diags_of(src, "E0315")[0]["expected"], "Int")

    def test_expression_size_e0314(self):
        for body, ret in (("return (1, 2, 3)", "(Int, Int)"), ("return (1, 2)", "(Int, Int, Int)"),
                          ("let q: (Int, Int) = (1, 2, 3)\nreturn q", "(Int, Int)")):
            with self.subTest(body=body):
                src = fn(body, params="", ret=ret, example="f() == f()")
                self.assertEqual(codes(src), ["E0314"])

    def test_returned_variable_of_wrong_size_e0314(self):
        src = fn("return p", ret="(Int, Int, Int)", example="f((1, 2)) == f((1, 2))")
        self.assertEqual(codes(src), ["E0314"])
        d = diags_of(src, "E0314")[0]
        self.assertEqual((d["expected"], d["found"]), ("(Int, Int, Int)", "(Int, Int)"))

    def test_argument_size_e0314(self):
        src = ('fn g(p: (Int, Int)) -> Int\n  example g((1, 2)) == 1\ndo\n  return 1\nend fn\n\n'
               'fn f() -> Int\n  example f() == 1\ndo\n  return g((1, 2, 3))\nend fn\n')
        self.assertEqual(codes(src), ["E0314"])

    def test_wrong_element_type_is_e0306_on_the_element(self):
        src = fn('return (1, 2)', params="", ret="(Int, Text)", example='f() == (1, "a")')
        self.assertEqual(codes(src), ["E0306"])
        d = diags_of(src, "E0306")[0]
        self.assertIn("tuple element 2", d["message"])
        self.assertEqual((d["expected"], d["found"]), ("Text", "Int"))

    def test_tuple_where_something_else_is_expected_is_e0306(self):
        src = fn("return (1, 2)", params="", ret="Int", example="f() == 1")
        self.assertEqual(codes(src), ["E0306"])
        self.assertEqual(diags_of(src, "E0306")[0]["found"], "(Int, Int)")

    def test_comparing_tuples_of_different_types(self):
        src = fn('return (1, 2) == (1, "a")', params="", ret="Bool", example="f() == false")
        self.assertEqual(codes(src), ["E0306"])
        src = fn("return (1, 2) == (1, 2, 3)", params="", ret="Bool", example="f() == false")
        self.assertEqual(codes(src), ["E0314"])

    def test_pattern_element_types_are_checked(self):
        src = fn('match p do\n  case (1, "x") =>\n    return 1\n  case _ =>\n    return 0\nend match')
        self.assertEqual(codes(src), ["E0306"])

    def test_pattern_bindings_take_the_element_types(self):
        src = fn("match p do\n  case (a, b) =>\n    return a + b\nend match")
        self.assertEqual(codes(src), [])
        src = fn('match p do\n  case (a, b) =>\n    return a + "x"\nend match')
        self.assertEqual(codes(src), ["E0306"])

    def test_tuple_types_print_like_the_source(self):
        bad = fn("return p", params="p: (Int, List<(Int, Text)>)", ret="Int", example="f((1, [])) == 1")
        got = diags_of(bad, "E0306")[0]
        self.assertEqual(got["found"], "(Int, List<(Int, Text)>)")
        self.assertNotIn("Tuple", got["message"])

    def test_field_access_on_a_tuple_value_is_still_a_record_error(self):
        src = fn("return p.x")
        self.assertEqual(codes(src), ["E0308"])


class ParseErrors(unittest.TestCase):
    def first(self, src):
        _, diags, _ = zehn.analyze(src)
        return diags[0]

    def test_destructuring_let_e0316(self):
        for kw in ("let", "var"):
            d = self.first(fn("%s (a, b) = p\nreturn a + b" % kw))
            self.assertEqual(d["code"], "E0316", kw)
            self.assertEqual(d["phase"], "parse")
            self.assertIn("match", d["fix_hint"])

    def test_index_access_e0317(self):
        for e in ("p.0", "p.1", "p.12"):
            self.assertEqual(self.first(fn("return " + e))["code"], "E0317", e)

    def test_empty_and_one_element_tuples_e0318(self):
        for e in ("()", "(1,)", "(1, 2,)", "(1, ())"):
            with self.subTest(expr=e):
                self.assertEqual(self.first(fn("let x = " + e + "\nreturn 1"))["code"], "E0318")

    def test_one_element_and_empty_patterns_and_types_e0318(self):
        for pat in ("(a)", "()", "(a,)", "(a, b,)"):
            with self.subTest(pattern=pat):
                src = fn("match p do\n  case %s =>\n    return 1\nend match" % pat)
                self.assertEqual(self.first(src)["code"], "E0318")
        for ty in ("(Int)", "()", "((Int))"):
            with self.subTest(type=ty):
                self.assertEqual(self.first(fn("return 1", params="p: " + ty))["code"], "E0318")

    def test_missing_close_paren_is_still_e0201(self):
        self.assertEqual(self.first(fn("return (1, 2"))["code"], "E0201")

    def test_existing_syntax_is_untouched(self):
        # a call with several arguments and a variant with several fields are not tuples
        src = ('type Shape = Rect(Int, Int)\n\nfn area(w: Int, h: Int) -> Int\n  example area(2, 3) == 6\n'
               'do\n  return w * h\nend fn\n\nfn g(s: Shape) -> Int\n  example g(Rect(2, 3)) == 6\ndo\n'
               '  match s do\n    case Rect(w, h) =>\n      return area(w, h)\n  end match\nend fn\n')
        self.assertEqual(codes(src), [])


class Formatting(unittest.TestCase):
    MESSY = ('fn f(p:(Int,Text),q: ( (Int,Int),Bool ))->(Text,Int)\n  example f((1,"a"),((1,2),true))==("a",1)\n'
             'do\n  match   (p,q)   do\n    case ((n,t),((a,_),true))=>\n      return (t,n)\n    case _ =>\n'
             '      return ("",0)\n  end match\nend fn\n')

    def test_canonical_text(self):
        out = format_program(zehn.parse(self.MESSY))
        self.assertIn("fn f(p: (Int, Text), q: ((Int, Int), Bool)) -> (Text, Int)", out)
        self.assertIn('example f((1, "a"), ((1, 2), true)) == ("a", 1)', out)
        self.assertIn("match (p, q) do", out)
        self.assertIn("case ((n, t), ((a, _), true)) =>", out)
        self.assertIn("return (t, n)", out)

    def test_idempotent(self):
        once = format_program(zehn.parse(self.MESSY))
        self.assertEqual(once, format_program(zehn.parse(once)))

    def test_parentheses_that_are_not_needed_disappear(self):
        out = format_program(zehn.parse(fn("return ((1 + 2), (3))", params="", ret="(Int, Int)",
                                           example="f() == (3, 3)")))
        self.assertIn("return (1 + 2, 3)", out)

    def test_precedence_around_tuples(self):
        out = format_program(zehn.parse(fn("return (1, 2) == (a, b)", params="a: Int, b: Int", ret="Bool",
                                           example="f(1, 2) == true")))
        self.assertIn("return (1, 2) == (a, b)", out)

    def test_example_file_is_canonical_and_idempotent(self):
        src = read("examples", "tuples.zehn")
        self.assertEqual(format_program(zehn.parse(src)), src)
        rc, out = cli("fmt", "examples/tuples.zehn", "--check")
        self.assertEqual(rc, 0, out)

    def test_hash_changes_with_a_tuple_element(self):
        a = zehn.definition_refs(zehn.parse(fn("return (1, 2)", params="", ret="(Int, Int)", example="f() == f()")))
        b = zehn.definition_refs(zehn.parse(fn("return (1, 3)", params="", ret="(Int, Int)", example="f() == f()")))
        self.assertNotEqual(a[0]["hash"], b[0]["hash"])


class Fuel(unittest.TestCase):
    def test_tuple_costs_one_step_plus_its_elements_like_a_list(self):
        _, tup = value("(a, 1, a + 1)", "a: Int", {"a": 5}.items())
        _, lst = value("[a, 1, a + 1]", "a: Int", {"a": 5}.items())
        self.assertEqual(tup, 1 + (1 + 1 + 3))
        self.assertEqual(tup, lst)

    def test_nested_tuple(self):
        _, n = value("(1, (2, 3))")
        self.assertEqual(n, 1 + 1 + (1 + 1 + 1))

    def test_pattern_matching_is_free(self):
        src = fn("match p do\n  case (a, b) =>\n    return 1\nend match", example="f((1, 2)) == 1")
        prog = zehn.parse(src)
        it = zehn.Interp(prog)
        it.invoke(prog.funcs["f"], [Tup((1, 2))])
        # match statement 1 + subject name 1 + body `return` 1 + literal 1
        self.assertEqual(it.used, 4)

    def test_fuel_runs_out_inside_a_tuple(self):
        prog = zehn.parse(fn("return (1, 2, 3, 4, 5, 6)", params="", ret="(Int, Int, Int, Int, Int, Int)",
                             example="f() == f()"))
        with self.assertRaises(zehn.ZehnError) as cm:
            zehn.Interp(prog, fuel=5).invoke(prog.funcs["f"], [])
        self.assertEqual(cm.exception.diag["code"], "E0801")


class Show(unittest.TestCase):
    def test_show(self):
        self.assertEqual(show(Tup((1, 2))), "(1, 2)")
        self.assertEqual(show(Tup(("a", True, [1, 2], Tup((3, 4))))), '("a", true, [1, 2], (3, 4))')
        self.assertEqual(show([Tup((1, 2)), Tup((3, 4))]), "[(1, 2), (3, 4)]")
        self.assertEqual(show(zehn.V("some", (Tup((1, 2)),))), "some((1, 2))")

    def test_failed_example_shows_tuples(self):
        src = fn("return (a, 0)", params="a: Int", ret="(Int, Int)", example="f(1) == (1, 1)")
        _, _, ex = zehn.analyze(src)
        self.assertEqual(ex[0]["status"], "fail")
        self.assertEqual(ex[0]["diag"]["values"]["left"], "(1, 0)")
        self.assertEqual(ex[0]["diag"]["values"]["right"], "(1, 1)")


class RunJson(unittest.TestCase):
    PATH = "examples/tuples.zehn"

    def run_(self, name, args):
        return cli("run", self.PATH, name, json.dumps(args))

    def test_tuple_argument_is_a_json_list(self):
        rc, out = self.run_("swap", [[1, "x"]])
        self.assertEqual((rc, out.strip()), (0, '("x", 1)'))

    def test_nested_tuple_argument(self):
        self.assertEqual(self.run_("span", [[[0, 0], [3, 4]]])[1].strip(), "7")

    def test_tuples_inside_list_option_and_variant(self):
        self.assertEqual(self.run_("sum_pairs", [[[1, 2], [3, 4]]])[1].strip(), "[3, 7]")
        self.assertEqual(self.run_("apply_move", [[1, 1], {"$": "Step", "args": [[2, -1]]}])[1].strip(), "(3, 0)")
        self.assertEqual(self.run_("apply_move", [[1, 1], {"$": "Stay"}])[1].strip(), "(1, 1)")

    def test_tuple_result_is_printed_with_show(self):
        self.assertEqual(self.run_("min_max", [5, 2])[1].strip(), "(2, 5)")
        self.assertEqual(self.run_("div_mod", [7, 2])[1].strip(), "ok((3, 1))")
        self.assertEqual(self.run_("labelled", [4])[1].strip(), '(4, (true, "even"))')

    def test_wrong_json_shape_is_a_caller_error(self):
        for bad in ([[1]], [[1, "x", 3]], [5], ["ab"], [{"a": 1}]):
            with self.subTest(arg=bad):
                rc, out = self.run_("swap", bad)
                d = json.loads(out)
                self.assertEqual((rc, d["code"], d.get("blame")), (1, "E0306", "caller"))

    def test_other_arguments_convert_as_before(self):
        rc, out = cli("run", "examples/shapes.zehn", "area", json.dumps([{"$": "Circle", "args": [2]}]))
        self.assertEqual(rc, 0, out)


class Registry(unittest.TestCase):
    def test_every_new_code_is_explained_and_has_a_catalog_entry(self):
        for code in NEW_CODES:
            with self.subTest(code=code):
                self.assertIn(code, EXPLAIN)
                base = os.path.join(ROOT, "catalog", code)
                for name in ("broken.zehn", "fixed.zehn", "meta.json"):
                    self.assertTrue(os.path.exists(os.path.join(base, name)), name)

    def test_explain_command(self):
        rc, out = cli("explain", "E0313")
        self.assertEqual(rc, 0)
        self.assertIn("tuple pattern", out)


class Files(unittest.TestCase):
    def test_example_passes_strict_with_examples(self):
        _, diags, ex = zehn.analyze(read("examples", "tuples.zehn"), strict=True)
        self.assertEqual([d["code"] for d in diags], [])
        self.assertTrue(ex and all(x["status"] == "pass" for x in ex))

    def test_error_file_produces_the_check_phase_codes(self):
        got = codes(read("errors", "bad_tuples.zehn"))
        for c in ("E0301", "E0306", "E0313", "E0314", "E0315"):
            self.assertIn(c, got)

    def test_error_file_is_canonical(self):
        rc, out = cli("fmt", "errors/bad_tuples.zehn", "--check")
        self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()
