"""TASK 05: dialect flags (zehnlib.dialect, --dialect, analyze(dialect=...))."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

from test_registry import ROOT, snapshot_registries

import zehn
from zehnlib import cli, dialect
from zehnlib.errors import ZehnError
from zehnlib.passes import static_pass
from zehnlib.stdlib import builtin

SHAPES = os.path.join(ROOT, "examples", "shapes.zehn")


def script(*args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py")] + list(args), cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return p.returncode, p.stdout


class Flags(unittest.TestCase):
    def setUp(self):
        snapshot_registries(self)
        dialect.flag("x", "a", ("a", "b", "c"), "demo flag")

    def test_no_flag_is_registered_by_the_package(self):
        dialect._FLAGS.clear()
        self.assertEqual(dialect.active(), {})

    def test_default_get_and_active(self):
        self.assertEqual(dialect.get("x"), "a")
        self.assertEqual(dialect.active(), {"effect_examples": "off", "int_ops": "operators", "x": "a"})   # + flags of TASK 06a, 06c
        active = dialect.active()
        active["x"] = "zzz"                                        # a copy: cannot change state
        self.assertEqual(dialect.get("x"), "a")

    def test_unknown_flag_get_is_a_keyerror(self):
        with self.assertRaises(KeyError):
            dialect.get("nope")

    def test_bad_registrations(self):
        with self.assertRaises(ValueError):
            dialect.flag("x", "a", ("a",), "again")                # duplicate
        with self.assertRaises(ValueError):
            dialect.flag("y", "z", ("a", "b"), "default not a choice")
        with self.assertRaises(ValueError):
            dialect.flag("a=b", "a", ("a",), "bad name")
        self.assertNotIn("y", dialect.active())

    def test_using_sets_and_restores(self):
        with dialect.using({"x": "b"}):
            self.assertEqual(dialect.get("x"), "b")
            with dialect.using({"x": "c"}):
                self.assertEqual(dialect.get("x"), "c")
            self.assertEqual(dialect.get("x"), "b")
        self.assertEqual(dialect.get("x"), "a")
        with dialect.using({}):
            self.assertEqual(dialect.get("x"), "a")

    def test_using_restores_state_on_error(self):
        with self.assertRaises(RuntimeError):
            with dialect.using({"x": "b"}):
                raise RuntimeError("boom")
        self.assertEqual(dialect.get("x"), "a")
        with dialect.using({"x": "b"}):
            with self.assertRaises(RuntimeError):
                with dialect.using({"x": "c"}):
                    raise RuntimeError("boom")
            self.assertEqual(dialect.get("x"), "b")                 # outer value restored, not default
        self.assertEqual(dialect.get("x"), "a")

    def test_using_validates_before_changing_anything(self):
        for bad in ({"nope": "a"}, {"x": "zzz"}, {"x": "b", "nope": "a"}):
            with self.subTest(bad=bad):
                with self.assertRaises(ZehnError) as cm:
                    with dialect.using(bad):
                        self.fail("body must not run")
                self.assertEqual(cm.exception.diag["code"], "E0001")
                self.assertEqual(dialect.get("x"), "a")

    def test_parse_cli(self):
        self.assertEqual(dialect.parse_cli([]), {})
        self.assertEqual(dialect.parse_cli(["x=b"]), {"x": "b"})
        self.assertEqual(dialect.parse_cli(["x=b", "x=c"]), {"x": "c"})   # repeated: last wins
        dialect.flag("y", "p", ("p", "q"), "second")
        self.assertEqual(dialect.parse_cli(["x=b", "y=q"]), {"x": "b", "y": "q"})

    def test_parse_cli_rejects_bad_input_with_e0001(self):
        for items in (["nope=1"], ["x=zzz"], ["x"], ["=b"], ["x=b", "nope=1"]):
            with self.subTest(items=items):
                with self.assertRaises(ZehnError) as cm:
                    dialect.parse_cli(items)
                self.assertEqual(cm.exception.diag["code"], "E0001")
                self.assertEqual(cm.exception.diag["phase"], "usage")


class WithAnalysis(unittest.TestCase):
    def setUp(self):
        snapshot_registries(self)
        dialect.flag("x", "a", ("a", "b"), "demo flag")

        @static_pass(410, "x_reporter")
        def reporter(prog, strict, prior):
            return [{"code": "W9100", "severity": "warning", "phase": "check",
                     "message": "x=%s" % dialect.get("x")}]

        @builtin("demo.x_is_b", "() -> Bool")
        def x_is_b(it):
            return dialect.get("x") == "b"

    SRC = "fn f() -> Bool\n  example f() == true\ndo\n  return demo.x_is_b()\nend fn\n"

    def messages(self, **kw):
        _, diags, ex = zehn.analyze(self.SRC, **kw)
        return [d["message"] for d in diags if d["code"] == "W9100"], ex

    def test_analyze_takes_dialect_as_its_last_parameter(self):
        import inspect
        params = list(inspect.signature(zehn.analyze).parameters)
        self.assertEqual(params, ["src", "strict", "path", "fuel", "max_depth", "guard", "dialect"])

    def test_default_and_override_and_restore(self):
        msgs, ex = self.messages()
        self.assertEqual(msgs, ["x=a"])
        self.assertEqual(ex[0]["status"], "fail")                  # example expects x == b
        msgs, ex = self.messages(dialect={"x": "b"})
        self.assertEqual(msgs, ["x=b"])
        self.assertEqual(ex[0]["status"], "pass")                  # visible on the guarded thread too
        msgs, ex = self.messages(dialect={"x": "b"}, guard=False)
        self.assertEqual(ex[0]["status"], "pass")
        self.assertEqual(dialect.get("x"), "a")                    # restored afterwards

    def test_analyze_with_a_bad_dialect_raises_and_restores(self):
        with self.assertRaises(ZehnError):
            zehn.analyze(self.SRC, dialect={"x": "zzz"})
        self.assertEqual(dialect.get("x"), "a")

    def test_cli_check_run_fmt_apply_the_flag(self):
        fd, path = tempfile.mkstemp(suffix=".zehn")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(self.SRC)
        self.addCleanup(os.remove, path)
        import io
        from contextlib import redirect_stdout

        def go(*argv):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cli.main(["zehn.py"] + list(argv))
            return rc, buf.getvalue()

        rc, out = go("check", path, "--json", "--dialect", "x=b")
        self.assertEqual(rc, 0)
        self.assertEqual([d["message"] for d in json.loads(out)["diagnostics"] if d["code"] == "W9100"],
                         ["x=b"])
        rc, out = go("check", path, "--json")
        self.assertEqual(rc, 1)                                    # example fails with the default
        self.assertEqual(go("run", path, "f", "[]", "--dialect", "x=b"), (0, "true\n"))
        self.assertEqual(go("run", path, "f", "[]"), (0, "false\n"))
        rc, out = go("fmt", path, "--check", "--dialect", "x=a", "--dialect", "x=b")   # repeatable
        self.assertEqual(rc, 0)
        self.assertEqual(dialect.get("x"), "a")


class CliErrors(unittest.TestCase):
    """No flag is registered by the package, so every --dialect is rejected: exit code 2."""

    def test_unknown_flag_is_exit_2_with_e0001(self):
        for cmd in (["check", SHAPES], ["run", SHAPES, "area", "[]"], ["fmt", SHAPES]):
            with self.subTest(cmd=cmd):
                rc, out = script(*cmd, "--dialect", "nope=1")
                self.assertEqual(rc, 2)
                d = json.loads(out)
                self.assertEqual(d["code"], "E0001")
                self.assertIn("nope", d["message"])

    def test_malformed_and_missing_value(self):
        self.assertEqual(script("check", SHAPES, "--dialect", "novalue")[0], 2)
        rc, out = script("check", SHAPES, "--dialect")
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["code"], "E0001")

    def test_without_the_option_nothing_changes(self):
        self.assertEqual(script("check", SHAPES)[0], 0)
        self.assertEqual(script("fmt", SHAPES, "--check")[0], 0)


if __name__ == "__main__":
    unittest.main()
