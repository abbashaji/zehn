"""TASK 06d: the diagnostics contract.

* every registered code has a catalog entry (catalog/<CODE>/broken.zehn, fixed.zehn, meta.json)
  and the entry behaves as its meta.json says;
* every diagnostic the catalog produces, and every `check --json` envelope, validates against
  docs/diagnostics.schema.json (checked by the small validator below: no jsonschema dependency);
* `check --json` starts with "schema": 1;
* tools/gen_error_docs.py is deterministic.

The test iterates the registry and the catalog folder, so a branch that adds a code together with
its catalog/<CODE>/ folder needs no edit here.

meta.json: {"strict": bool, "dialect": {flag: value}, "note": "one line"} plus, for codes that
`analyze` cannot show, one of
  "cli": [argv with {file} and {dir}], "cli_fixed": [argv]   run `zehn.py <argv>` (usage and patch
                                                             codes, and run-time codes that need
                                                             JSON arguments or a missing grant)
  "unreachable": "reason" [, "probe": {"fn", "args", "grant"}]  a defensive guard that the static
                                                             passes make unreachable from check/run
"""
from __future__ import annotations

import collections
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import zehn  # noqa: E402  (imports zehnlib, which fills the registries)
from zehnlib.cli import main, to_value  # noqa: E402
from zehnlib.errors import EXPLAIN, ZehnError  # noqa: E402

CATALOG = os.path.join(ROOT, "catalog")
SCHEMA_PATH = os.path.join(ROOT, "docs", "diagnostics.schema.json")
ZEHN_PY = os.path.join(ROOT, "zehn.py")

# The v0.3 codes: the ones whose explain texts this task reviewed (other branches' texts are theirs).
V03_CODES = (
    "E0001 E0101 E0201 E0202 E0203 E0204 E0301 E0302 E0303 E0304 E0305 E0306 E0307 E0308 E0309 E0310 "
    "E0401 E0402 E0501 E0502 E0503 E0504 E0505 E0506 E0507 E0601 E0602 E0603 E0604 E0701 E0702 E0703 "
    "E0801 E0802 W0101 W0102 W0201 W0301").split()


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ----------------------------------------------------------------------------
# A small JSON Schema (draft-07 subset) validator: $ref (local), type, enum, const, required,
# properties, additionalProperties, items, minimum, minLength, pattern. Other keywords are ignored.
# ----------------------------------------------------------------------------

def _is_type(value, name):
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "null":
        return value is None
    raise ValueError("unsupported type %r in schema" % name)


def validate(instance, schema, root=None, path="$"):
    """Return a list of error strings (empty when `instance` satisfies `schema`)."""
    root = root if root is not None else schema
    errors = []
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError("only local $ref is supported, got %r" % ref)
        target = root
        for part in ref[2:].split("/"):
            target = target[part]
        return validate(instance, target, root, path)
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(instance, n) for n in names):
            return ["%s: expected %s, got %s" % (path, "/".join(names), type(instance).__name__)]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append("%s: %r is not one of %r" % (path, instance, schema["enum"]))
    if "const" in schema:
        c = schema["const"]
        if instance != c or isinstance(instance, bool) != isinstance(c, bool):
            errors.append("%s: expected the constant %r, got %r" % (path, c, instance))
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append("%s: shorter than %d" % (path, schema["minLength"]))
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append("%s: %r does not match %s" % (path, instance, schema["pattern"]))
    if _is_type(instance, "number") and "minimum" in schema and instance < schema["minimum"]:
        errors.append("%s: %r is below %r" % (path, instance, schema["minimum"]))
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in instance:
                errors.append("%s: missing required key %r" % (path, key))
        for key, value in instance.items():
            if key in props:
                errors += validate(value, props[key], root, "%s.%s" % (path, key))
            elif schema.get("additionalProperties", True) is False:
                errors.append("%s: unexpected key %r" % (path, key))
            elif isinstance(schema.get("additionalProperties"), dict):
                errors += validate(value, schema["additionalProperties"], root, "%s.%s" % (path, key))
    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            errors += validate(item, schema["items"], root, "%s[%d]" % (path, i))
    return errors


def load_schema():
    return json.loads(read(SCHEMA_PATH))


def diagnostic_errors(diag):
    schema = load_schema()
    return validate(diag, schema["definitions"]["diagnostic"], schema)


# ----------------------------------------------------------------------------
# The catalog
# ----------------------------------------------------------------------------

def entry(code):
    d = os.path.join(CATALOG, code)
    return {"dir": d, "meta": json.loads(read(os.path.join(d, "meta.json"))),
            "broken": read(os.path.join(d, "broken.zehn")), "fixed": read(os.path.join(d, "fixed.zehn"))}


def catalog_folders():
    return sorted(n for n in os.listdir(CATALOG) if os.path.isdir(os.path.join(CATALOG, n)))


def analysis(e, kind):
    """(diagnostics, failed example diagnostics) of broken/fixed through `analyze`, with the stored
    strict flag and dialect. The path is given so a `.lock` file next to the program is honoured."""
    path = os.path.join(e["dir"], kind + ".zehn")
    _, diags, examples = zehn.analyze(e[kind], e["meta"].get("strict", False), path,
                                      dialect=e["meta"].get("dialect") or {})
    return list(diags), [x["diag"] for x in examples if x["status"] == "fail"]


def cli(e, kind, key=None):
    """Run `zehn.py <argv>` for a meta "cli" / "cli_fixed" entry; returns (exit code, stdout, stderr)."""
    argv = e["meta"][key or ("cli" if kind == "broken" else "cli_fixed")]
    path = os.path.join(e["dir"], kind + ".zehn")
    argv = [a.replace("{file}", path).replace("{dir}", e["dir"]) for a in argv]
    p = subprocess.run([sys.executable, ZEHN_PY] + argv, cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    return p.returncode, p.stdout, p.stderr


def probe(e, kind):
    """Run an "unreachable" entry's guard by calling the interpreter on the program WITHOUT the
    static passes. Returns the list of diagnostics that raised (empty when everything passed)."""
    prog = zehn.parse(e[kind])
    p = e["meta"].get("probe")
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink):
            if p:
                it = zehn.Interp(prog, granted=p.get("grant", []))
                it.fresh_budget()
                it.call_fn(prog.funcs[p["fn"]], [to_value(a) for a in p.get("args", [])])
                return []
            return [x["diag"] for x in zehn.Interp(prog).run_examples() if x["status"] == "fail"]
    except ZehnError as z:
        return [z.diag]


def json_diags(text):
    """Diagnostic dicts in a CLI's stdout: one JSON object or a list of them."""
    try:
        out = json.loads(text)
    except ValueError:
        return []
    return [d for d in (out if isinstance(out, list) else [out]) if isinstance(d, dict) and "code" in d]


def codes_of(diags, failed):
    return [d["code"] for d in diags] + [d["code"] for d in failed]


class CatalogCompleteness(unittest.TestCase):
    def test_every_registered_code_has_a_catalog_folder_and_the_reverse(self):
        self.assertEqual(catalog_folders(), sorted(EXPLAIN))

    def test_v03_codes_are_all_registered(self):
        self.assertEqual(sorted(set(V03_CODES) - set(EXPLAIN)), [])

    def test_folder_contents(self):
        for code in sorted(EXPLAIN):
            with self.subTest(code=code):
                for name in ("broken.zehn", "fixed.zehn", "meta.json"):
                    self.assertTrue(os.path.isfile(os.path.join(CATALOG, code, name)), name)
                meta = entry(code)["meta"]
                self.assertIsInstance(meta["strict"], bool)
                self.assertIsInstance(meta["dialect"], dict)
                self.assertTrue(meta["note"].strip() and "\n" not in meta["note"])
                if "cli" in meta:
                    self.assertIsInstance(meta["cli"], list)
                    self.assertIsInstance(meta["cli_fixed"], list)
                    self.assertTrue(any("{file}" in a for a in meta["cli"] + meta["cli_fixed"]))
                self.assertFalse("cli" in meta and "unreachable" in meta)

    def test_explain_texts_exist_and_v03_texts_are_short(self):
        for code in sorted(EXPLAIN):
            self.assertTrue(EXPLAIN[code].strip(), code)
        for code in V03_CODES:
            with self.subTest(code=code):
                self.assertLess(len(EXPLAIN[code].split()), 60)

    def test_zehn_explain_knows_every_code(self):
        for code in sorted(EXPLAIN):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["zehn.py", "explain", code])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), EXPLAIN[code].strip())


class CatalogBehaviour(unittest.TestCase):
    def test_broken_and_fixed_behave_as_the_meta_says(self):
        for code in sorted(EXPLAIN):
            with self.subTest(code=code):
                e = entry(code)
                meta = e["meta"]
                if "cli" in meta:
                    self.check_cli(code, e)
                elif "unreachable" in meta:
                    self.check_unreachable(code, e)
                else:
                    self.check_analysis(code, e)

    def check_analysis(self, code, e):
        self.assertNotEqual(e["broken"], e["fixed"])
        diags, failed = analysis(e, "broken")
        self.assertIn(code, codes_of(diags, failed), "broken.zehn does not show %s" % code)
        self.assertEqual(next(d for d in diags + failed if d["code"] == code)["severity"],
                         "error" if code.startswith("E") else "warning")
        diags, failed = analysis(e, "fixed")
        self.assertEqual([d["code"] for d in diags if d["severity"] == "error"], [])
        self.assertEqual([d["code"] for d in failed], [])
        self.assertNotIn(code, codes_of(diags, failed))

    def check_cli(self, code, e):
        rc, out, err = cli(e, "broken")
        self.assertNotEqual(rc, 0, out + err)
        self.assertIn('"code": "%s"' % code, out + err)
        rc, out, err = cli(e, "fixed")
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn('"code": "%s"' % code, out + err)

    def check_unreachable(self, code, e):
        # 1. through the front door the program is rejected by a different check, never by this code
        diags, failed = analysis(e, "broken")
        self.assertNotIn(code, codes_of(diags, failed))
        self.assertTrue([d for d in diags if d["severity"] == "error"], "the static passes must reject it")
        # 2. the guard itself fires when the static passes are skipped
        self.assertIn(code, [d["code"] for d in probe(e, "broken")])
        # 3. the fixed program is clean both ways
        diags, failed = analysis(e, "fixed")
        self.assertEqual([d["code"] for d in diags if d["severity"] == "error"], [])
        self.assertEqual(probe(e, "fixed"), [])

    def test_usage_errors_exit_with_2_and_the_others_with_1(self):
        rc, out, _ = cli(entry("E0001"), "broken")
        self.assertEqual(rc, 2)
        rc, out, _ = cli(entry("E0701"), "broken")
        self.assertEqual(rc, 1)

    def test_e0204_on_the_command_line_needs_a_lower_recursion_limit(self):
        path = os.path.join(CATALOG, "E0204", "broken.zehn")
        p = subprocess.run([sys.executable, ZEHN_PY, "check", path, "--json", "--max-depth", "100"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual([d["code"] for d in json.loads(p.stdout)["diagnostics"]], ["E0204"])

    def test_the_lock_files_of_w0201_match_their_programs(self):
        # the drift is only visible with the .lock next to the program
        d = os.path.join(CATALOG, "W0201")
        self.assertTrue(os.path.isfile(os.path.join(d, "broken.zehn.lock")))
        self.assertTrue(os.path.isfile(os.path.join(d, "fixed.zehn.lock")))


class SchemaTests(unittest.TestCase):
    def test_validator_accepts_and_rejects(self):
        s = {"type": "object", "required": ["a"], "additionalProperties": False,
             "properties": {"a": {"type": "integer", "minimum": 1}, "b": {"type": ["string", "null"]},
                            "c": {"const": 1}, "d": {"enum": ["x", "y"]}, "e": {"type": "array", "items": {"type": "string"}},
                            "f": {"type": "string", "pattern": "^[EW][0-9]{4}$"}}}
        self.assertEqual(validate({"a": 1, "b": None, "c": 1, "d": "x", "e": ["q"], "f": "E0001"}, s), [])
        for bad in ({}, {"a": True}, {"a": 0}, {"a": 1, "z": 1}, {"a": 1, "b": 2}, {"a": 1, "c": True},
                    {"a": 1, "d": "z"}, {"a": 1, "e": [1]}, {"a": 1, "f": "X1"}):
            self.assertNotEqual(validate(bad, s), [], bad)

    def test_schema_file_is_a_draft_07_document(self):
        s = load_schema()
        self.assertEqual(s["$schema"], "http://json-schema.org/draft-07/schema#")
        self.assertEqual(s["required"], ["schema", "ok", "diagnostics", "definitions", "examples"])
        d = s["definitions"]["diagnostic"]
        self.assertEqual(d["required"], ["code", "severity", "phase", "message"])
        for key in ("location", "fix_hint", "blame", "values", "falls_through", "call_stack", "via_example"):
            self.assertIn(key, d["properties"])
        self.assertIs(d["additionalProperties"], True)
        self.assertEqual(sorted(s["definitions"]["location"]["properties"]), ["clause", "fn", "line"])

    def test_extra_keys_are_allowed_but_required_ones_are_not_optional(self):
        d = {"code": "E0001", "severity": "error", "phase": "usage", "message": "m", "future_key": [1, 2]}
        self.assertEqual(diagnostic_errors(d), [])
        for missing in ("code", "severity", "phase", "message"):
            bad = dict(d)
            del bad[missing]
            self.assertNotEqual(diagnostic_errors(bad), [], missing)
        self.assertNotEqual(diagnostic_errors(dict(d, severity="fatal")), [])
        self.assertNotEqual(diagnostic_errors(dict(d, code="X0001")), [])

    def test_every_catalog_diagnostic_validates(self):
        seen = collections.Counter()
        for code in sorted(EXPLAIN):
            e = entry(code)
            for kind in ("broken", "fixed"):
                with self.subTest(code=code, kind=kind):
                    if "cli" in e["meta"]:
                        _, out, err = cli(e, kind)
                        diags = json_diags(out)
                    elif "unreachable" in e["meta"]:
                        diags = probe(e, kind) + sum(analysis(e, kind), [])
                    else:
                        diags = sum(analysis(e, kind), [])
                    for d in diags:
                        self.assertEqual(diagnostic_errors(d), [], d)
                        seen[d["code"]] += 1
        # the catalog must really exercise the diagnostics it claims to (not an empty loop)
        for code in sorted(EXPLAIN):
            self.assertGreater(seen[code], 0, "no catalog diagnostic with code %s was validated" % code)

    def run_check(self, args):
        buf = io.StringIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)    # cmd_check leaves the source file to the GC
            with contextlib.redirect_stdout(buf):
                rc = main(["zehn.py", "check"] + args)
            import gc
            gc.collect()
        return rc, buf.getvalue()

    def test_check_json_envelopes_validate(self):
        schema = load_schema()
        programs = []
        for folder in ("examples", "errors"):
            for name in sorted(os.listdir(os.path.join(ROOT, folder))):
                if name.endswith(".zehn"):
                    programs.append((os.path.join(ROOT, folder, name), []))
        for code in sorted(EXPLAIN):
            e = entry(code)
            if "cli" in e["meta"] or "unreachable" in e["meta"]:
                continue
            for kind in ("broken", "fixed"):
                args = [os.path.join(e["dir"], kind + ".zehn")] + (["--strict"] if e["meta"]["strict"] else [])
                for flag, value in sorted(e["meta"].get("dialect", {}).items()):
                    args += ["--dialect", "%s=%s" % (flag, value)]
                if code == "E0204" and kind == "broken":
                    args += ["--max-depth", "100"]
                programs.append((args[0], args[1:]))
        for path, extra in programs:
            with self.subTest(program=os.path.relpath(path, ROOT)):
                _, out = self.run_check([path, "--json"] + extra)
                doc = json.loads(out)
                self.assertEqual(validate(doc, schema), [])
                for r in doc["examples"]["results"]:
                    self.assertEqual(r["status"] == "fail", "diag" in r)

    def test_check_json_starts_with_schema_1(self):
        for rel in ("examples/shapes.zehn", "errors/bad_static.zehn", "catalog/E0001/broken.zehn"):
            with self.subTest(program=rel):
                p = subprocess.run([sys.executable, ZEHN_PY, "check", os.path.join(ROOT, rel), "--json"],
                                   cwd=ROOT, stdout=subprocess.PIPE, universal_newlines=True)
                doc = json.loads(p.stdout, object_pairs_hook=collections.OrderedDict)
                self.assertEqual(list(doc)[0], "schema")
                self.assertEqual(doc["schema"], 1)
                self.assertIs(type(doc["schema"]), int)
                self.assertTrue(p.stdout.startswith('{\n  "schema": 1,'))

    def test_docs_describe_the_compatibility_rule(self):
        text = read(os.path.join(ROOT, "docs", "DIAGNOSTICS.md"))
        self.assertIn("only ever added", text)
        self.assertIn("docs/diagnostics.schema.json", text)


class GeneratorTests(unittest.TestCase):
    def test_two_runs_are_byte_identical_and_cover_every_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = os.path.join(tmp, "a.md"), os.path.join(tmp, "b.md")
            for out in (a, b):
                p = subprocess.run([sys.executable, os.path.join(TOOLS, "gen_error_docs.py"), "--out", out],
                                   cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                self.assertEqual(p.returncode, 0, p.stderr)
            with open(a, "rb") as fa, open(b, "rb") as fb:
                da, db = fa.read(), fb.read()
            self.assertEqual(da, db)
            text = da.decode("utf-8")
            for code in EXPLAIN:
                self.assertIn("\n## %s\n" % code, text)
            self.assertNotIn(b"\r", da)

    def test_severity_and_phase_come_from_the_real_diagnostic(self):
        import gen_error_docs
        for code in sorted(EXPLAIN):
            with self.subTest(code=code):
                d = gen_error_docs.observe(code, gen_error_docs.entry(code))
                self.assertIsNotNone(d, "the broken program does not produce %s" % code)
                self.assertEqual(d["severity"], "error" if code.startswith("E") else "warning")


if __name__ == "__main__":
    unittest.main()
