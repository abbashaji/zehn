"""TASK 05: registries (stdlib, static passes, commands, explain texts) and discovery.

This module also holds the helpers the other TASK 05 test files import: `snapshot_registries`
(restore every registry when a test ends, so a test can register temporary things without leaking
them into other tests) and `make_package` (a temporary package on sys.path)."""
from __future__ import annotations

import importlib
import io
import json
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import zehn  # noqa: E402  (imports zehnlib, which fills the registries)
import zehnlib  # noqa: E402
from zehnlib import cli, dialect, errors, passes, stdlib  # noqa: E402
from zehnlib.passes import run_static, static_pass  # noqa: E402
from zehnlib.stdlib import builtin  # noqa: E402


def _containers():
    return [stdlib.BUILTINS, stdlib.SIGS, stdlib.COSTS, stdlib.EFFECTS, stdlib.NAMESPACES,
            stdlib.RESERVED, passes.PASSES, cli.COMMANDS, dialect._FLAGS, dialect._VALUES,
            errors.EXPLAIN, errors.HINTS]


def snapshot_registries(testcase):
    """Restore every registry when the test ends (cleanups run after tearDown)."""
    saved = [(c, list(c) if isinstance(c, list) else c.copy()) for c in _containers()]

    def restore():
        for c, copy in saved:
            c.clear()
            if isinstance(c, list):
                c.extend(copy)
            else:
                c.update(copy)

    testcase.addCleanup(restore)


def make_package(testcase, name, files):
    """Create a package `name` in a temp dir on sys.path with the given {filename: source};
    returns the imported package. Removed again (dir, sys.path, sys.modules) at cleanup."""
    root = tempfile.mkdtemp(prefix="zehn_plugin_")
    pkg = os.path.join(root, name)
    os.makedirs(pkg)
    with open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8") as fh:
        fh.write("")
    for fname, src in files.items():
        with open(os.path.join(pkg, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(textwrap.dedent(src))
    sys.path.insert(0, root)

    def cleanup():
        sys.path.remove(root)
        for m in [m for m in sys.modules if m == name or m.startswith(name + ".")]:
            del sys.modules[m]
        importlib.invalidate_caches()
        shutil.rmtree(root, ignore_errors=True)

    testcase.addCleanup(cleanup)
    importlib.invalidate_caches()
    return importlib.import_module(name)


DEMO_PLUGIN = '''
    """One new file adds a stdlib function, a static pass and a command."""
    from __future__ import annotations

    from zehnlib.cli import command
    from zehnlib.passes import static_pass
    from zehnlib.stdlib import builtin

    SEEN = []        # len(prior) the pass saw, one entry per run


    @builtin("demo.double", "(Int) -> Int")
    def _double(it, n):
        return n * 2


    @builtin("demo.total", "(List<Int>) -> Int", cost="linear")
    def _total(it, xs):
        return sum(xs)


    @builtin("demo.pair", "(List<Int>) -> Int", cost=lambda a: (5, 7))
    def _pair(it, xs):
        return len(xs)


    @builtin("demo.stamp", "() -> Int", effect="demo.fx")
    def _stamp(it):
        return 42


    @static_pass(450, "demo_tmp_names")
    def _tmp_names(prog, strict, prior):
        SEEN.append(len(prior))
        return [{"code": "W9901", "severity": "warning", "phase": "check",
                 "message": "function %r has a tmp_ name" % f.name,
                 "location": {"fn": f.name, "line": f.line}}
                for f in prog.funcs.values() if f.name.startswith("tmp_")]


    @command("demo", "demo    <word>")
    def _demo(argv):
        print("demo:" + argv[0])
        return 7
'''


def prog_src(body, name="f", params="x: Int", ret="Int", example="f(1) == 2", uses=""):
    return ("fn %s(%s) -> %s\n%s  example %s\ndo\n  return %s\nend fn\n"
            % (name, params, ret, ("  uses [%s]\n" % uses) if uses else "", example, body))


def codes(src):
    _, diags, ex = zehn.analyze(src)
    return sorted({d["code"] for d in diags} | {x["diag"]["code"] for x in ex if x["status"] == "fail"})


class Recording(zehn.Interp):
    """Interp that records every explicit charge (stdlib costs, big-int arithmetic)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.charges = []

    def tick(self, line, n=1):
        self.charges.append(n)
        super().tick(line, n)


def run_fn(src, name, args):
    prog = zehn.parse(src)
    it = Recording(prog, granted=["demo.fx"])
    return it.invoke(prog.funcs[name], args), it


class StdlibRegistry(unittest.TestCase):
    def setUp(self):
        snapshot_registries(self)

    def test_exports(self):
        for name in ("BUILTINS", "SIGS", "COSTS", "NAMESPACES", "RESERVED", "EFFECTS"):
            self.assertTrue(hasattr(stdlib, name), name)
        self.assertEqual(set(stdlib.BUILTINS), set(stdlib.SIGS))
        self.assertEqual(set(stdlib.BUILTINS), set(stdlib.COSTS))
        self.assertEqual(stdlib.RESERVED, stdlib.NAMESPACES | stdlib.CTORS | {"out"})
        self.assertEqual(stdlib.NAMESPACES,
                         {"console", "int", "list", "map", "option", "result", "text", "time"})
        self.assertEqual(stdlib.EFFECTS, {"console.print": "console", "time.now": "time.now"})
        self.assertIs(zehn.BUILTINS, stdlib.BUILTINS)      # the facade shares the registry
        self.assertIs(zehn.SIGS, stdlib.SIGS)

    def test_duplicate_name_raises_and_changes_nothing(self):
        before = (dict(stdlib.BUILTINS), dict(stdlib.SIGS), dict(stdlib.COSTS))
        with self.assertRaises(ValueError):
            builtin("list.len", "(List<A>) -> Int")
        with self.assertRaises(ValueError):
            @builtin("list.len", "(List<A>) -> Int")
            def again(it, xs):
                return 0
        self.assertEqual((stdlib.BUILTINS, stdlib.SIGS, stdlib.COSTS), before)
        @builtin("demo.once", "() -> Int")
        def once(it):
            return 1
        with self.assertRaises(ValueError):
            builtin("demo.once", "() -> Int")

    def test_bad_registrations_raise(self):
        for args, kw in [(("nodot", "() -> Int"), {}), (("a.b.c", "() -> Int"), {}),
                         (("demo.x", "(Nope) -> Int"), {}), (("demo.x", "() -> Int"), {"cost": "heavy"}),
                         (("ok.x", "() -> Int"), {}), (("out.x", "() -> Int"), {}),
                         (("demo.x", "() -> Int"), {"effect": 3})]:
            with self.subTest(args=args, kw=kw):
                with self.assertRaises(ValueError):
                    builtin(*args, **kw)
        self.assertNotIn("demo", stdlib.NAMESPACES)

    def test_registration_updates_namespaces_and_reserved_in_place(self):
        ns, res = stdlib.NAMESPACES, stdlib.RESERVED
        @builtin("demo.double", "(Int) -> Int")
        def double(it, n):
            return n * 2
        self.assertIs(ns, stdlib.NAMESPACES)
        self.assertIn("demo", ns)
        self.assertIn("demo", res)
        # a reserved namespace cannot be used as a variable name
        self.assertIn("E0307", codes(prog_src("1", params="demo: Int")))

    def test_registered_function_type_checks_runs_and_is_charged_as_declared(self):
        @builtin("demo.double", "(Int) -> Int")
        def double(it, n):
            return n * 2
        @builtin("demo.total", "(List<Int>) -> Int", cost="linear")
        def total(it, xs):
            return sum(xs)
        @builtin("demo.pair", "(List<Int>) -> Int", cost=lambda a: (5, 7))
        def pair(it, xs):
            return len(xs)
        @builtin("demo.one", "(Int) -> Int", cost=lambda a: 9)
        def one(it, n):
            return n
        good = prog_src("demo.double(x)")
        self.assertEqual(codes(good), [])
        self.assertEqual(codes(prog_src("demo.double(\"a\")")), ["E0306"])        # type-checked
        self.assertEqual(codes(prog_src("demo.double(x, x)")), ["E0303"])        # arity
        self.assertEqual(codes(prog_src("demo.nope(x)")), ["E0302"])             # unknown name
        out, it = run_fn(good, "f", [21])
        self.assertEqual(out, 42)
        self.assertEqual(it.charges, [])                                        # flat: no extra charge
        xs = "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
        out, it = run_fn(prog_src("demo.total(%s)" % xs), "f", [0])
        self.assertEqual((out, it.charges), (55, [10]))                         # linear: sum of sizes
        out, it = run_fn(prog_src("demo.pair(%s)" % xs), "f", [0])
        self.assertEqual((out, it.charges), (10, [5, 7]))                       # callable: tuple, in order
        out, it = run_fn(prog_src("demo.one(x)"), "f", [3])
        self.assertEqual((out, it.charges), (3, [9]))                           # callable: single int

    def test_charges_count_against_the_fuel_budget(self):
        @builtin("demo.pair", "(List<Int>) -> Int", cost=lambda a: (50, 50))
        def pair(it, xs):
            return len(xs)
        prog = zehn.parse(prog_src("demo.pair([1])"))
        base = zehn.Interp(prog)
        base.invoke(prog.funcs["f"], [0])
        self.assertGreaterEqual(base.used, 100)
        tight = zehn.Interp(prog, fuel=base.used - 1)
        with self.assertRaises(zehn.ZehnError) as cm:
            tight.invoke(prog.funcs["f"], [0])
        self.assertEqual(cm.exception.diag["code"], "E0801")

    def test_int_to_text_keeps_its_two_charges_in_order(self):
        src = prog_src("int.to_text(x)", ret="Text", example='f(1) == "1"')
        out, it = run_fn(src, "f", [2 ** 200])
        self.assertEqual(it.charges, [3, 4])           # size 3 words: linear 3, then (3+1)**2 // 4
        self.assertEqual(len(out), 61)

    def test_effect_is_declared_checked_and_granted(self):
        @builtin("demo.stamp", "() -> Int", effect="demo.fx")
        def stamp(it):
            return 42
        self.assertIn("E0601", codes(prog_src("demo.stamp()", params="", example="f() == 42")))
        ok = prog_src("demo.stamp()", params="", example="1 == 1", uses="demo.fx")
        self.assertEqual(codes(ok), [])
        prog = zehn.parse(ok)
        with self.assertRaises(zehn.ZehnError) as cm:                           # host did not grant
            zehn.Interp(prog).invoke(prog.funcs["f"], [])
        self.assertEqual(cm.exception.diag["code"], "E0604")
        self.assertEqual(zehn.Interp(prog, granted=["demo.fx"]).invoke(prog.funcs["f"], []), 42)


class PassRegistry(unittest.TestCase):
    def setUp(self):
        snapshot_registries(self)

    def test_v03_passes_and_their_orders(self):
        self.assertEqual([(o, n) for o, n, _ in passes.PASSES],
                         [(100, "names"), (200, "types"), (300, "returns"), (400, "recursion"), (410, "int_ops"),
                          (420, "effect_examples")])

    def test_static_diags_is_run_static(self):
        with open(os.path.join(ROOT, "errors", "bad_types.zehn"), encoding="utf-8") as fh:
            src = fh.read()
        prog = zehn.parse(src)
        self.assertEqual(zehn.static_diags(prog), run_static(prog))
        self.assertTrue(zehn.static_diags(prog))

    def test_passes_run_in_ascending_order_and_see_prior(self):
        seen = []

        @static_pass(420, "late")
        def late(prog, strict, prior):
            seen.append(("late", strict, [d["code"] for d in prior]))
            return [{"code": "W9002", "severity": "warning", "phase": "check", "message": "late"}]

        @static_pass(410, "early")
        def early(prog, strict, prior):
            seen.append(("early", strict, [d["code"] for d in prior]))
            return [{"code": "W9001", "severity": "warning", "phase": "check", "message": "early"}]

        src = "fn f() -> Int\ndo\n  return 1\nend fn\n"       # no example: W0101 from `names`
        out = run_static(zehn.parse(src), strict=False)
        codes_out = [d["code"] for d in out]
        self.assertEqual(codes_out, ["W0101", "W9001", "W9002"])
        self.assertEqual(seen, [("early", False, ["W0101"]), ("late", False, ["W0101", "W9001"])])
        run_static(zehn.parse(src), strict=True)
        self.assertTrue(seen[-1][1])                             # strict is passed through

    def test_order_ties_break_by_name_and_duplicates_raise(self):
        order = []
        for nm in ("b_pass", "a_pass"):
            static_pass(430, nm)(lambda p, s, prior, nm=nm: order.append(nm) or [])
        run_static(zehn.parse("fn f() -> Int\ndo\n  return 1\nend fn\n"))
        self.assertEqual(order, ["a_pass", "b_pass"])
        with self.assertRaises(ValueError):
            static_pass(440, "a_pass")
        with self.assertRaises(ValueError):
            static_pass("440", "x")

    def test_prior_is_a_copy(self):
        @static_pass(410, "mutator")
        def mutator(prog, strict, prior):
            prior.append({"code": "X", "severity": "error"})
            return []
        out = run_static(zehn.parse("fn f() -> Int\ndo\n  return 1\nend fn\n"))
        self.assertNotIn("X", [d["code"] for d in out])

    def test_types_pass_skips_functions_the_names_pass_rejected(self):
        src = ("fn f(x: Int) -> Int\n  example f(1) == 1\ndo\n  return y + \"a\"\nend fn\n")
        self.assertEqual(codes(src), ["E0302"])                  # no cascade of E0306


class ExplainRegistry(unittest.TestCase):
    def setUp(self):
        snapshot_registries(self)

    def test_texts_are_registered_and_duplicates_raise(self):
        self.assertIn("E0301", errors.EXPLAIN)
        self.assertIn("E0801", errors.HINTS)
        with self.assertRaises(ValueError):
            errors.explain("E0301", "again")
        with self.assertRaises(ValueError):
            errors.hint("E0801", "again")
        before = len(errors.EXPLAIN)      # not a literal: every new code (TASK 06d on) adds an entry
        errors.explain("E9999", "demo text")
        self.assertEqual(run_cli(["explain", "E9999"])[1].strip(), "demo text")
        self.assertEqual(len(errors.EXPLAIN), before + 1)


def run_cli(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(["zehn.py"] + argv)
    return rc, buf.getvalue()


class CommandRegistry(unittest.TestCase):
    def setUp(self):
        snapshot_registries(self)

    def test_discovery_lists_all_seven_commands(self):
        self.assertEqual(sorted(cli.COMMANDS),
                         ["check", "explain", "fmt", "hash", "lock", "patch", "run"])
        rc, out = run_cli(["--help"])
        self.assertEqual(rc, 0)
        for name in cli.COMMANDS:
            self.assertIn("zehn.py %s " % name, out)
        self.assertEqual(sum(1 for ln in out.splitlines() if ln.startswith("    zehn.py ")), 9)

    def test_help_from_the_real_script(self):
        import subprocess
        p = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py"), "--help"],
                           stdout=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(p.returncode, 0)
        for name in ("check", "run", "fmt", "hash", "lock", "patch", "explain"):
            self.assertIn("zehn.py %s " % name, p.stdout)

    def test_usage_errors_keep_exit_code_2(self):
        self.assertEqual(run_cli([])[0], 2)
        self.assertEqual(run_cli(["bogus", "x"])[0], 2)
        self.assertEqual(run_cli(["run", "examples/shapes.zehn"])[0], 2)
        self.assertEqual(run_cli(["patch", "examples/shapes.zehn"])[0], 2)

    def test_duplicate_command_raises(self):
        with self.assertRaises(ValueError):
            cli.command("check", "check x")(lambda argv: 0)

    def test_registered_command_gets_args_after_the_subcommand(self):
        got = []
        cli.command("echo", "echo <x>")(lambda argv: got.append(argv) or 0)
        self.assertEqual(run_cli(["echo", "a", "--b"])[0], 0)
        self.assertEqual(got, [["a", "--b"]])


class Discovery(unittest.TestCase):
    def setUp(self):
        snapshot_registries(self)

    def test_discover_imports_submodules_in_sorted_name_order(self):
        pkg = make_package(self, "zdisc_order", {
            "b_two.py": "import sys\nsys.modules['zdisc_order'].ORDER.append('b_two')\n",
            "a_one.py": "import sys\nsys.modules['zdisc_order'].ORDER.append('a_one')\n",
            "c_three.py": "import sys\nsys.modules['zdisc_order'].ORDER.append('c_three')\n",
        })
        pkg.ORDER = []
        mods = zehnlib.discover(pkg)
        self.assertEqual(pkg.ORDER, ["a_one", "b_two", "c_three"])
        self.assertEqual([m.__name__ for m in mods],
                         ["zdisc_order.a_one", "zdisc_order.b_two", "zdisc_order.c_three"])
        zehnlib.discover(pkg)                                   # idempotent: modules import once
        self.assertEqual(pkg.ORDER, ["a_one", "b_two", "c_three"])

    def test_builtin_registries_were_discovered_on_import(self):
        self.assertEqual(len(stdlib.BUILTINS), 39)
        self.assertEqual(len(cli.COMMANDS), 7)
        self.assertEqual(len(passes.PASSES), 6)


class DemoPlugin(unittest.TestCase):
    """A feature is one new file: it registers a stdlib function, a static pass and a command."""

    def setUp(self):
        snapshot_registries(self)
        self.pkg = make_package(self, "zdemo_plugin", {"feature.py": DEMO_PLUGIN})

    def load(self):
        zehnlib.discover(self.pkg)
        return sys.modules["zdemo_plugin.feature"]

    def test_nothing_is_registered_before_discovery(self):
        self.assertNotIn("demo.double", stdlib.BUILTINS)
        self.assertNotIn("demo", cli.COMMANDS)
        self.assertEqual(len(passes.PASSES), 6)

    def test_stdlib_function_type_checks_runs_and_is_charged(self):
        self.load()
        src = prog_src("demo.double(x)")
        self.assertEqual(codes(src), [])
        self.assertEqual(codes(prog_src("demo.double(\"a\")")), ["E0306"])
        out, it = run_fn(src, "f", [4])
        self.assertEqual(out, 8)
        xs = "[1, 2, 3]"
        self.assertEqual(run_fn(prog_src("demo.total(%s)" % xs), "f", [0])[1].charges, [3])
        self.assertEqual(run_fn(prog_src("demo.pair(%s)" % xs), "f", [0])[1].charges, [5, 7])
        self.assertIn("E0601", codes(prog_src("demo.stamp()", params="", example="1 == 1")))
        self.assertEqual(run_fn(prog_src("demo.stamp()", params="", example="1 == 1", uses="demo.fx"),
                                "f", [])[0], 42)

    def test_static_pass_runs_after_the_builtin_passes_and_sees_their_output(self):
        feat = self.load()
        self.assertEqual([n for _, n, _ in passes.PASSES],
                         ["names", "types", "returns", "recursion", "int_ops", "effect_examples",
                          "demo_tmp_names"])
        src = prog_src("1", name="tmp_helper", params="", example="tmp_helper() == 1")
        _, diags, _ = zehn.analyze(src)
        self.assertEqual([d["code"] for d in diags], ["W9901"])
        feat.SEEN.clear()
        zehn.analyze("fn g() -> Int\ndo\n  return 1\nend fn\n")        # W0101 from `names`
        self.assertEqual(feat.SEEN, [1])

    def test_command_is_dispatched_with_its_own_usage_line(self):
        self.load()
        self.assertEqual(run_cli(["demo", "hello"]), (7, "demo:hello\n"))
        rc, out = run_cli(["--help"])
        self.assertIn("zehn.py demo    <word>", out)

    def test_everything_goes_away_with_the_snapshot_restore(self):
        self.load()
        self.assertIn("demo.double", stdlib.BUILTINS)
        # (restored by addCleanup; the next test class proves it by checking the counts)


class NoLeaks(unittest.TestCase):
    def test_registries_are_back_to_the_builtin_state(self):
        self.assertEqual(len(stdlib.BUILTINS), 39)
        self.assertNotIn("demo", stdlib.NAMESPACES)
        self.assertEqual(len(passes.PASSES), 6)
        self.assertEqual(sorted(cli.COMMANDS),
                         ["check", "explain", "fmt", "hash", "lock", "patch", "run"])


if __name__ == "__main__":
    unittest.main()
