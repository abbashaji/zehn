"""Tests for the ts_strict, rust and rust_strict adapters (TASK 01d).

The adapters are tested directly (not through run.py). Tests that need an external tool call
`toolchain_missing()` first: if a tool is not installed they are skipped with the reason, and the
install commands are in bench/langs/README.md. Stdlib only, Python 3.9+.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest import mock

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))

from benchlib.adapters import REGISTRY  # noqa: E402
from benchlib.adapters import rust as rust_mod  # noqa: E402
from benchlib.adapters import ts_strict as ts_mod  # noqa: E402

FIXTURES = HERE / "fixtures" / "toolchains"

SHARED_DIGESTS = {
    "benchlib/__init__.py": "dd98e9c77e18908649e28e2d2b17f5fd0f369d3b6ce35f58d25bed9dc94e46a5",
    "benchlib/adapters/base.py": "f2b4c5c5b9da7e0688929826a672d8a48ee1ca40c469429d83e4571939fc61c1",
    "benchlib/adapters/__init__.py": "9544043583b111a305e4e8129e1ae92b6ad7162f26520a3efb34fb89699a1e64",
}


def load(slug: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    task = json.loads((FIXTURES / slug / "task.json").read_text(encoding="utf-8"))
    tests = json.loads((FIXTURES / slug / "tests.json").read_text(encoding="utf-8"))
    return task, tests


def source(slug: str, stem: str, ext: str) -> str:
    return (FIXTURES / slug / (stem + ext)).read_text(encoding="utf-8")


# ---------------------------------------------------------------- no external tool needed

class SharedFileTests(unittest.TestCase):
    def test_sha256_of_shared_files(self) -> None:
        for rel, want in SHARED_DIGESTS.items():
            got = hashlib.sha256((BENCH / rel).read_bytes()).hexdigest()
            self.assertEqual(got, want, rel)

    def test_registry_has_the_three_adapters(self) -> None:
        for name, ext in (("ts_strict", ".ts"), ("rust", ".rs"), ("rust_strict", ".rs")):
            self.assertIn(name, REGISTRY)
            self.assertEqual(REGISTRY[name].name, name)
            self.assertEqual(REGISTRY[name].ext, ext)

    def test_new_python_files_follow_project_constraints(self) -> None:
        files = [BENCH / "benchlib/adapters/ts_strict.py", BENCH / "benchlib/adapters/rust.py",
                 BENCH / "benchlib/adapters/rust_strict.py", Path(__file__).resolve()]
        for path in files:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src, feature_version=(3, 9))
            body = tree.body
            first = body[1] if isinstance(body[0], ast.Expr) else body[0]
            self.assertIsInstance(first, ast.ImportFrom, path.name)
            self.assertEqual(first.module, "__future__", path.name)
            self.assertNotIn("\r", src, path.name)

    def test_text_files_use_lf(self) -> None:
        for root in (BENCH / "langs", FIXTURES):
            for path in root.rglob("*"):
                if path.is_file():
                    self.assertNotIn(b"\r", path.read_bytes(), str(path))

    def test_fixture_tasks_are_complete(self) -> None:
        slugs = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir())
        self.assertEqual(len(slugs), 8)
        for slug in slugs:
            task, tests = load(slug)
            for key in ("id", "category", "level", "kind", "title", "description", "entry", "params", "returns",
                        "types", "effects", "visible_examples", "notes"):
                self.assertIn(key, task, slug)
            self.assertGreaterEqual(len(tests), 8, slug)
            for ext in (".ts", ".rs"):
                self.assertTrue((FIXTURES / slug / ("ref" + ext)).is_file(), slug)
            if "console" in task["effects"]:
                self.assertTrue(all("stdout" in t for t in tests), slug)


class UnavailableToolTests(unittest.TestCase):
    def test_all_tools_missing(self) -> None:
        with mock.patch("shutil.which", return_value=None):
            ok, why = REGISTRY["ts_strict"].available()
            self.assertFalse(ok)
            self.assertIn("tsc", why)
            self.assertIn("node", why)
            ok, why = REGISTRY["rust"].available()
            self.assertFalse(ok)
            self.assertIn("cargo", why)
            ok, why = REGISTRY["rust_strict"].available()
            self.assertFalse(ok)
            for tool in ("cargo-clippy", "cargo-fmt", "rustfmt"):
                self.assertIn(tool, why)

    def test_only_one_tool_missing_is_named(self) -> None:
        def which(name: str) -> Any:
            return None if name == "tsc" else "/usr/bin/" + name
        with mock.patch("shutil.which", side_effect=which):
            ok, why = REGISTRY["ts_strict"].available()
            self.assertFalse(ok)
            self.assertIn("tsc", why)
            self.assertNotIn("node", why)

    def test_everything_present(self) -> None:
        with mock.patch("shutil.which", side_effect=lambda n: "/usr/bin/" + n):
            for name in ("ts_strict", "rust", "rust_strict"):
                self.assertEqual(REGISTRY[name].available(), (True, ""))

    def test_system_prompts_name_the_signature(self) -> None:
        task, _ = load("record_richest")
        for name in ("ts_strict", "rust", "rust_strict"):
            text = REGISTRY[name].system_prompt(task)
            self.assertIn("richest", text)
            self.assertIn("Account", text)
        self.assertIn("fn richest(accts: Vec<Account>) -> Option<Account>", REGISTRY["rust"].system_prompt(task))
        self.assertIn("clippy", REGISTRY["rust_strict"].system_prompt(task))
        self.assertNotIn("clippy", REGISTRY["rust"].system_prompt(task))
        console, _ = load("console_greet")
        self.assertIn("console.log", REGISTRY["ts_strict"].system_prompt(console))
        self.assertIn("println!", REGISTRY["rust"].system_prompt(console))


class ValueMappingTests(unittest.TestCase):
    """One test per value kind: canonical JSON of the expected value and the literal given to the program."""

    def setUp(self) -> None:
        task, _ = load("record_richest")
        self.env = rust_mod._TypeEnv(task)
        self.p = self.env.parse

    def canon(self, type_text: str, value: Any) -> str:
        return rust_mod.canon(self.env, self.p(type_text), value)

    def rs(self, type_text: str, value: Any) -> str:
        return rust_mod._rs_lit(self.env, self.p(type_text), value)

    def ts(self, type_text: str, value: Any) -> str:
        return ts_mod._ts_lit(self.env, self.p(type_text), value)

    def test_int(self) -> None:
        self.assertEqual(self.canon("Int", -5), "-5")
        self.assertEqual(self.rs("Int", -5), "-5i64")
        self.assertEqual(self.ts("Int", -5), "(-5)")
        self.assertEqual(self.rs("Int", 2 ** 63 - 1), "9223372036854775807i64")
        for bad in (2 ** 63, -2 ** 63 - 1, True, 1.5, "1"):
            with self.assertRaises(ValueError):
                self.canon("Int", bad)
        with self.assertRaises(ValueError):
            self.ts("Int", 2 ** 53)
        self.assertEqual(self.ts("Int", 2 ** 53 - 1), str(2 ** 53 - 1))

    def test_bool(self) -> None:
        self.assertEqual(self.canon("Bool", True), "true")
        self.assertEqual(self.rs("Bool", False), "false")
        self.assertEqual(self.ts("Bool", True), "true")
        with self.assertRaises(ValueError):
            self.canon("Bool", 1)

    def test_text(self) -> None:
        self.assertEqual(self.canon("Text", 'a"b\\c\n'), '"a\\"b\\\\c\\n"')
        self.assertEqual(self.rs("Text", 'a"b\\c\n\t'), '::std::string::String::from("a\\"b\\\\c\\n\\t")')
        self.assertEqual(self.ts("Text", 'a"b'), '"a\\"b"')
        self.assertEqual(self.rs("Text", "\x01"), '::std::string::String::from("\\u{1}")')
        for t in ("Text",):
            with self.assertRaises(ValueError):
                self.canon(t, "caf\u00e9")

    def test_list(self) -> None:
        self.assertEqual(self.canon("List<Int>", [1, 2]), "[1,2]")
        self.assertEqual(self.rs("List<Int>", []), "::std::vec::Vec::<i64>::new()")
        self.assertEqual(self.rs("List<Int>", [1, -2]), "::std::vec![1i64, -2i64]")
        self.assertEqual(self.ts("List<Int>", [1, 2]), "[1, 2]")
        self.assertEqual(self.ts("List<Int>", []), "[]")
        self.assertEqual(self.canon("List<List<Text>>", [["a"], []]), '[["a"],[]]')

    def test_option(self) -> None:
        none, some = {"$": "none"}, {"$": "some", "args": [3]}
        self.assertEqual(self.canon("Option<Int>", none), '{"$":"none"}')
        self.assertEqual(self.canon("Option<Int>", some), '{"$":"some","args":[3]}')
        self.assertEqual(self.rs("Option<Int>", none), "::std::option::Option::<i64>::None")
        self.assertEqual(self.rs("Option<Int>", some), "::std::option::Option::Some(3i64)")
        self.assertEqual(self.ts("Option<Int>", none), "null")
        self.assertEqual(self.ts("Option<Int>", some), "3")
        with self.assertRaises(ValueError):
            self.p("Option<Option<Int>>")

    def test_result(self) -> None:
        ok, err = {"$": "ok", "args": [3]}, {"$": "err", "args": ["x"]}
        self.assertEqual(self.canon("Result<Int, Text>", ok), '{"$":"ok","args":[3]}')
        self.assertEqual(self.canon("Result<Int, Text>", err), '{"$":"err","args":["x"]}')
        head = "::std::result::Result::<i64, ::std::string::String>::"
        self.assertEqual(self.rs("Result<Int, Text>", ok), head + "Ok(3i64)")
        self.assertEqual(self.rs("Result<Int, Text>", err), head + 'Err(::std::string::String::from("x"))')
        self.assertEqual(self.ts("Result<Int, Text>", ok), "{ ok: true, value: 3 }")
        self.assertEqual(self.ts("Result<Int, Text>", err), '{ ok: false, error: "x" }')
        with self.assertRaises(ValueError):
            self.p("Result<Int, Int>")

    def test_record(self) -> None:
        acct = {"active": True, "balance": 1, "owner": "a"}   # key order must not matter
        self.assertEqual(self.canon("Account", acct), '{"owner":"a","balance":1,"active":true}')
        self.assertEqual(self.rs("Account", acct),
                         'Account { owner: ::std::string::String::from("a"), balance: 1i64, active: true }')
        self.assertEqual(self.ts("Account", acct), '{ "owner": "a", "balance": 1, "active": true }')
        for bad in ({"owner": "a", "balance": 1}, dict(acct, extra=1)):
            with self.assertRaises(ValueError):
                self.canon("Account", bad)

    def test_unknown_type_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.p("Map<Int, Int>")

    def test_markers_separate_stdout_from_result(self) -> None:
        tests = [{"args": [], "expect": 5, "stdout": "hello"}, {"args": [], "expect": 6}]
        out = "\x01B0\x02hello\x01E0\x025\x03\x01B1\x02ignored\x01E1\x026\x03"
        res = rust_mod._score(tests, ["5", "6"], out, "", 0.0)
        self.assertEqual((res["passed"], res["total"], res["failures"]), (2, 2, []))
        res = rust_mod._score(tests, ["5", "6"], out.replace("hello", "bye"), "", 0.0)
        self.assertEqual(res["passed"], 1)
        self.assertEqual(res["failures"][0]["index"], 0)
        res = rust_mod._score(tests, ["5", "6"], "\x01B0\x02hello\x01E0\x025\x03", "", 0.0)
        self.assertEqual(res["failures"], [{"index": 1, "got": "<no result>", "want": "6"}])
        res = rust_mod._score([{"args": [], "expect": 1}], ["1"], "\x01B0\x02\x01E0\x02true\x03", "", 0.0)
        self.assertEqual(res["passed"], 0)   # true is not 1


# ---------------------------------------------------------------- tests that run the real tools

class _AdapterCases(object):
    """Shared checks; a concrete class sets `adapter_name` and `unknown_code`."""
    adapter_name = ""
    unknown_code = ""

    def toolchain_missing(self) -> None:
        ok, why = self.adapter.available()
        if not ok:
            self.skipTest("toolchain_missing: " + why)

    def setUp(self) -> None:
        self.adapter = REGISTRY[self.adapter_name]
        self.toolchain_missing()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = tmp.name
        self.ext = self.adapter.ext

    # helpers
    def check(self, slug: str, stem: str) -> Dict[str, Any]:
        task, _ = load(slug)
        return self.adapter.tool_check(task, source(slug, stem, self.ext), self.work)

    def hidden(self, slug: str, stem: str) -> Dict[str, Any]:
        task, tests = load(slug)
        return self.adapter.run_hidden(task, source(slug, stem, self.ext), tests, self.work)

    def assert_kind(self, slug: str) -> None:
        chk = self.check(slug, "ref")
        self.assertTrue(chk["ok"], chk["diagnostics"])
        self.assertEqual(chk["diagnostics"], [])
        self.assertIsInstance(chk["tool_ms"], int)
        _, tests = load(slug)
        res = self.hidden(slug, "ref")
        self.assertEqual(res["total"], len(tests))
        self.assertEqual(res["passed"], res["total"], res["failures"])
        self.assertEqual(res["failures"], [])
        self.assertIsInstance(res["ms"], int)

    # one test per value kind
    def test_kind_int(self) -> None:
        self.assert_kind("int_add")

    def test_kind_bool(self) -> None:
        self.assert_kind("bool_is_even")

    def test_kind_text(self) -> None:
        self.assert_kind("text_shout")

    def test_kind_list(self) -> None:
        self.assert_kind("list_double")

    def test_kind_option(self) -> None:
        self.assert_kind("option_first_even")

    def test_kind_result(self) -> None:
        self.assert_kind("result_safe_div")

    def test_kind_record(self) -> None:
        self.assert_kind("record_richest")

    def test_kind_console_stdout(self) -> None:
        self.assert_kind("console_greet")

    # failure modes
    def test_type_error_is_not_ok_and_has_a_line(self) -> None:
        chk = self.check("int_add", "type_error")
        self.assertFalse(chk["ok"])
        lines = [d["line"] for d in chk["diagnostics"] if d["line"] is not None]
        self.assertTrue(lines, chk["diagnostics"])
        self.assertEqual(lines[0], 2)
        self.assertEqual(self.hidden("int_add", "type_error")["passed"], 0)

    def test_unknown_name_is_flagged(self) -> None:
        chk = self.check("int_add", "unknown_name")
        self.assertFalse(chk["ok"])
        flagged = [d for d in chk["diagnostics"] if d["unknown_name"]]
        self.assertEqual([d["code"] for d in flagged], [self.unknown_code])
        self.assertEqual(flagged[0]["line"], 2)
        self.assertFalse([d for d in self.check("int_add", "type_error")["diagnostics"] if d["unknown_name"]])

    def test_wrong_values_build_but_fail_tests(self) -> None:
        self.assertTrue(self.check("int_add", "wrong")["ok"])
        res = self.hidden("int_add", "wrong")
        self.assertEqual(res["total"], 9)
        self.assertTrue(0 < res["passed"] < res["total"], res)
        self.assertEqual(len(res["failures"]), res["total"] - res["passed"])
        first = res["failures"][0]
        self.assertEqual(sorted(first), ["got", "index", "want"])
        self.assertEqual((first["index"], first["got"], first["want"]), (0, "-1", "3"))

    def test_crash_scores_zero(self) -> None:
        self.assertTrue(self.check("int_add", "crash")["ok"])
        res = self.hidden("int_add", "crash")
        self.assertEqual(res["passed"], 0)
        self.assertEqual(res["total"], 9)
        self.assertIn("crashed", res["failures"][0]["got"])
        self.assertIn("boom", res["failures"][0]["got"])

    def test_timeout_scores_zero(self) -> None:
        with mock.patch.object(self.adapter, "run_timeout", 2.0):
            res = self.hidden("int_add", "loop")
        self.assertEqual(res["passed"], 0)
        self.assertIn("timed out", res["failures"][0]["got"])

    def test_signature_mismatch_is_caught_without_a_line(self) -> None:
        chk = self.check("int_add", "sig_mismatch")
        self.assertFalse(chk["ok"])
        self.assertTrue(all(d["line"] is None and not d["unknown_name"] for d in chk["diagnostics"]))
        self.assertIn("entry point check", chk["diagnostics"][0]["message"])
        self.assertEqual(self.hidden("int_add", "sig_mismatch")["passed"], 0)

    def test_wrong_console_output_fails_the_test(self) -> None:
        self.assertTrue(self.check("console_greet", "wrong_stdout")["ok"])
        res = self.hidden("console_greet", "wrong_stdout")
        self.assertEqual(res["passed"], 0)    # the return values are right, the printed text is not
        self.assertIn("stdout=", res["failures"][0]["got"])
        self.assertIn('"Hello, Ann!\\n"', res["failures"][0]["want"])

    def test_diagnostic_shape(self) -> None:
        chk = self.check("int_add", "type_error")
        self.assertTrue(chk["diagnostics"])
        for d in chk["diagnostics"]:
            self.assertEqual(sorted(d), ["code", "line", "message", "raw", "unknown_name"])
            self.assertIsInstance(d["code"], str)
            self.assertIsInstance(d["message"], str)
            self.assertTrue(d["line"] is None or isinstance(d["line"], int))
            self.assertIsInstance(d["unknown_name"], bool)
            self.assertIsInstance(d["raw"], str)

    def test_empty_program_is_rejected(self) -> None:
        task, _ = load("int_add")
        chk = self.adapter.tool_check(task, "", self.work)
        self.assertFalse(chk["ok"])
        self.assertTrue(chk["diagnostics"])

    def test_crlf_and_missing_final_newline(self) -> None:
        task, tests = load("int_add")
        code = source("int_add", "ref", self.ext).replace("\n", "\r\n").rstrip("\r\n")
        self.assertTrue(self.adapter.tool_check(task, code, self.work)["ok"])
        self.assertEqual(self.adapter.run_hidden(task, code, tests, self.work)["passed"], 9)

    def test_repeated_calls_in_one_workdir_follow_the_code(self) -> None:
        # the runner iterates in one work directory: no result may leak from an earlier program
        self.assertTrue(self.check("int_add", "ref")["ok"])
        self.assertEqual(self.hidden("int_add", "ref")["passed"], 9)
        self.assertFalse(self.check("int_add", "type_error")["ok"])
        self.assertEqual(self.hidden("int_add", "type_error")["passed"], 0)
        self.assertTrue(self.check("int_add", "ref")["ok"])
        self.assertEqual(self.hidden("int_add", "wrong")["passed"], 2)


class TsStrictTests(_AdapterCases, unittest.TestCase):
    adapter_name = "ts_strict"
    unknown_code = "TS2304"

    def test_strict_flags_are_active(self) -> None:
        cases = [("int_add", "implicit_any", "TS7006"),
                 ("option_first_even", "unchecked_index", "TS2322"),   # noUncheckedIndexedAccess
                 ("int_add", "no_implicit_return", "TS7030"),
                 ("int_add", "fallthrough", "TS7029")]
        for slug, stem, code in cases:
            with self.subTest(stem):
                chk = self.check(slug, stem)
                self.assertFalse(chk["ok"])
                self.assertIn(code, [d["code"] for d in chk["diagnostics"]])
                self.assertTrue(all(isinstance(d["line"], int) for d in chk["diagnostics"]))

    def test_model_may_declare_names_that_clash_with_dom_types(self) -> None:
        task, tests = load("text_shout")
        code = "type Text = string;\n\nfunction shout(s: Text): Text {\n  return s.toUpperCase() + \"!\";\n}\n"
        self.assertTrue(self.adapter.tool_check(task, code, self.work)["ok"])
        self.assertEqual(self.adapter.run_hidden(task, code, tests, self.work)["passed"], len(tests))


class RustTests(_AdapterCases, unittest.TestCase):
    adapter_name = "rust"
    unknown_code = "E0425"

    def test_plain_build_accepts_unformatted_and_clippy_warnings(self) -> None:
        for stem in ("unformatted", "clippy_warn", "clippy_and_unformatted"):
            with self.subTest(stem):
                self.assertTrue(self.check("int_add", stem)["ok"])
                self.assertEqual(self.hidden("int_add", stem)["passed"], 9)

    def test_other_unknown_name_codes(self) -> None:
        task, _ = load("int_add")
        cases = [("E0433", "fn add(a: i64, b: i64) -> i64 {\n    Foo::bar(a, b)\n}\n"),
                 ("E0412", "fn add(a: i64, b: Missing) -> i64 {\n    a\n}\n"),
                 ("E0599", "fn add(a: i64, b: i64) -> i64 {\n    a.nope(b)\n}\n")]
        for code, src in cases:
            with self.subTest(code):
                chk = self.adapter.tool_check(task, src, self.work)
                self.assertFalse(chk["ok"])
                self.assertEqual([d["code"] for d in chk["diagnostics"] if d["unknown_name"]], [code])

    def test_missing_entry_function_is_not_a_hallucination(self) -> None:
        task, _ = load("int_add")
        chk = self.adapter.tool_check(task, "fn other(a: i64) -> i64 {\n    a\n}\n", self.work)
        self.assertFalse(chk["ok"])
        self.assertEqual(chk["diagnostics"][0]["code"], "E0425")
        self.assertFalse(chk["diagnostics"][0]["unknown_name"])
        self.assertIsNone(chk["diagnostics"][0]["line"])

    def test_private_items_and_keyword_fields_are_reachable(self) -> None:
        task = {"entry": "pick", "params": [{"name": "x", "type": "Thing"}], "returns": "Thing",
                "types": [{"name": "Thing", "fields": [{"name": "type", "type": "Text"}, {"name": "n", "type": "Int"}]}]}
        code = "struct Thing {\n    r#type: String,\n    n: i64,\n}\n\nfn pick(x: Thing) -> Thing {\n    x\n}\n"
        tests = [{"args": [{"type": "t", "n": i}], "expect": {"type": "t", "n": i}} for i in range(8)]
        res = self.adapter.run_hidden(task, code, tests, self.work)
        self.assertEqual((res["passed"], res["total"]), (8, 8), res["failures"])


class RustStrictTests(_AdapterCases, unittest.TestCase):
    adapter_name = "rust_strict"
    unknown_code = "E0425"

    def test_unformatted_but_correct_is_rejected(self) -> None:
        chk = self.check("int_add", "unformatted")
        self.assertFalse(chk["ok"])
        self.assertEqual([d["code"] for d in chk["diagnostics"]], ["fmt"])
        self.assertEqual(chk["diagnostics"][0]["line"], 1)
        self.assertIn("expected: fn add(a: i64, b: i64) -> i64 {", chk["diagnostics"][0]["message"])
        self.assertFalse(chk["diagnostics"][0]["unknown_name"])

    def test_clippy_warning_is_rejected(self) -> None:
        chk = self.check("int_add", "clippy_warn")
        self.assertFalse(chk["ok"])
        self.assertEqual([d["code"] for d in chk["diagnostics"]], ["clippy::needless_return"])
        self.assertEqual(chk["diagnostics"][0]["line"], 2)

    def test_clippy_and_format_problems_are_both_reported(self) -> None:
        chk = self.check("int_add", "clippy_and_unformatted")
        self.assertFalse(chk["ok"])
        self.assertEqual(sorted(d["code"] for d in chk["diagnostics"]), ["clippy::needless_return", "fmt"])

    def test_compiler_warnings_fail_under_deny_warnings(self) -> None:
        task, _ = load("int_add")
        unused = "fn add(a: i64, b: i64) -> i64 {\n    let unused = 1;\n    a + b\n}\n"
        chk = self.adapter.tool_check(task, unused, self.work)
        self.assertFalse(chk["ok"])
        self.assertEqual([(d["code"], d["line"]) for d in chk["diagnostics"]], [("unused_variables", 2)])
        dead = "fn helper() {}\n\nfn add(a: i64, b: i64) -> i64 {\n    a + b\n}\n"
        chk = self.adapter.tool_check(task, dead, self.work)
        self.assertEqual([(d["code"], d["line"]) for d in chk["diagnostics"]], [("dead_code", 1)])

    def test_hidden_tests_measure_behaviour_not_style(self) -> None:
        for stem in ("unformatted", "clippy_warn"):
            self.assertEqual(self.hidden("int_add", stem)["passed"], 9)

    def test_clippy_is_not_cached_away_between_calls(self) -> None:
        for _ in range(2):
            self.assertFalse(self.check("int_add", "clippy_warn")["ok"])
            self.assertTrue(self.check("int_add", "ref")["ok"])

    def test_plain_rust_adapter_is_unaffected(self) -> None:
        plain = REGISTRY["rust"]
        task, _ = load("int_add")
        self.assertTrue(plain.tool_check(task, source("int_add", "clippy_warn", ".rs"), self.work)["ok"])


if __name__ == "__main__":
    unittest.main()
