"""Task / tests / record validation and the task loader (stdlib only, Python 3.9+)."""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

CATEGORIES = ("pure", "text", "domain", "effect", "edit")
KINDS = ("write", "edit")
EFFECTS = ("console",)
MIN_TESTS = 8
INT_MIN, INT_MAX = -(2 ** 63), 2 ** 63 - 1
RECORD_SCHEMA_VERSION = 1

_IDENT = re.compile(r"^[a-z][a-z0-9_]*$")
_TYPE_NAME = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_TASK_ID = re.compile(r"^([a-z]+)_(\d{3})$")
_PRIMS = ("Int", "Bool", "Text")
_RESERVED = set(_PRIMS) | {"List", "Option", "Result", "Map", "Unit"}

# A parsed type is a tuple: ("Int",) ("Bool",) ("Text",) ("List", t) ("Option", t)
# ("Result", t, ("Text",)) ("Rec", name).
Type = Tuple[Any, ...]


class TaskError(Exception):
    """A task directory that cannot be loaded or does not validate."""


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

_TOKEN = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*|<|>|,|\(|\)|->)")


def _tokens(text: str) -> List[str]:
    out: List[str] = []
    pos = 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError("unexpected character %r in type %r" % (text[pos], text))
        out.append(m.group(1))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return out


def parse_type(text: str, records: Optional[Dict[str, Any]] = None) -> Type:
    """Parse a Zehn-syntax type from the allowed set. Raises ValueError with the reason."""
    records = records or {}
    toks = _tokens(text)
    if not toks:
        raise ValueError("empty type")
    pos = [0]

    def peek() -> Optional[str]:
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take(expect: Optional[str] = None) -> str:
        t = peek()
        if t is None or (expect is not None and t != expect):
            raise ValueError("expected %r in type %r" % (expect or "a type", text))
        pos[0] += 1
        return t

    def one(inside_option: bool) -> Type:
        t = take()
        if t in _PRIMS:
            return (t,)
        if t == "List":
            take("<")
            inner = one(False)
            take(">")
            return ("List", inner)
        if t == "Option":
            if inside_option:
                raise ValueError("nested Option is not allowed in %r" % text)
            take("<")
            inner = one(True)
            take(">")
            return ("Option", inner)
        if t == "Result":
            take("<")
            ok = one(False)
            take(",")
            err = one(False)
            take(">")
            if err != ("Text",):
                raise ValueError("Result error type must be Text in %r" % text)
            return ("Result", ok, err)
        if t in ("Map", "Unit"):
            raise ValueError("type %s is not allowed in the bench (in %r)" % (t, text))
        if t == "(" or t == "Fn":
            raise ValueError("tuple and function types are not allowed (in %r)" % text)
        if t in records:
            return ("Rec", t)
        raise ValueError("unknown type %r (declare it under \"types\" or use Int/Bool/Text/List/Option/Result)" % t)

    result = one(False)
    if pos[0] != len(toks):
        raise ValueError("trailing text in type %r" % text)
    return result


def type_text(t: Type) -> str:
    """Back to Zehn syntax."""
    if t[0] in _PRIMS:
        return t[0]
    if t[0] == "Rec":
        return t[1]
    if t[0] == "Result":
        return "Result<%s, %s>" % (type_text(t[1]), type_text(t[2]))
    return "%s<%s>" % (t[0], type_text(t[1]))


def record_map(task: Dict[str, Any]) -> Dict[str, Dict[str, Type]]:
    """{record name: {field: parsed type}} (assumes the task validated)."""
    names = {r["name"]: r for r in task.get("types", [])}
    return {n: {f["name"]: parse_type(f["type"], names) for f in r["fields"]} for n, r in names.items()}


# ---------------------------------------------------------------------------
# JSON values vs types
# ---------------------------------------------------------------------------

def check_value(v: Any, t: Type, recs: Dict[str, Dict[str, Type]], path: str = "$") -> List[str]:
    """Errors for a JSON value that does not conform to type t (encoding in the task spec)."""
    k = t[0]
    if k == "Int":
        if isinstance(v, bool) or not isinstance(v, int):
            return ["%s: expected Int, got %r" % (path, v)]
        if not INT_MIN <= v <= INT_MAX:
            return ["%s: Int %d does not fit signed 64-bit" % (path, v)]
        return []
    if k == "Bool":
        return [] if isinstance(v, bool) else ["%s: expected Bool, got %r" % (path, v)]
    if k == "Text":
        if not isinstance(v, str):
            return ["%s: expected Text, got %r" % (path, v)]
        if any(ord(c) > 127 for c in v):
            return ["%s: Text must be ASCII" % path]
        return []
    if k == "List":
        if not isinstance(v, list):
            return ["%s: expected List, got %r" % (path, v)]
        errs: List[str] = []
        for i, x in enumerate(v):
            errs += check_value(x, t[1], recs, "%s[%d]" % (path, i))
        return errs
    if k in ("Option", "Result"):
        if not isinstance(v, dict) or "$" not in v:
            return ["%s: expected a {\"$\": ...} value for %s, got %r" % (path, k, v)]
        tag, args = v["$"], v.get("args", [])
        extra = set(v) - {"$", "args"}
        if extra:
            return ["%s: unexpected keys %s" % (path, sorted(extra))]
        if k == "Option":
            if tag == "none":
                return [] if args == [] else ["%s: none takes no args" % path]
            if tag == "some" and isinstance(args, list) and len(args) == 1:
                return check_value(args[0], t[1], recs, path + ".some")
            return ["%s: bad Option value %r" % (path, v)]
        if tag in ("ok", "err") and isinstance(args, list) and len(args) == 1:
            return check_value(args[0], t[1] if tag == "ok" else t[2], recs, path + "." + tag)
        return ["%s: bad Result value %r" % (path, v)]
    if k == "Rec":
        fields = recs[t[1]]
        if not isinstance(v, dict):
            return ["%s: expected record %s, got %r" % (path, t[1], v)]
        if set(v) != set(fields):
            return ["%s: record %s needs exactly the fields %s, got %s" % (path, t[1], sorted(fields), sorted(v))]
        errs = []
        for name, ft in fields.items():
            errs += check_value(v[name], ft, recs, path + "." + name)
        return errs
    return ["%s: unsupported type %r" % (path, t)]


# ---------------------------------------------------------------------------
# Task and tests validation
# ---------------------------------------------------------------------------

def validate_task(task: Any, fixture: bool = False) -> List[str]:
    """Errors (empty list = valid). `fixture` relaxes only the id/category prefix rule."""
    if not isinstance(task, dict):
        return ["task.json must be an object"]
    errs: List[str] = []
    for key in ("id", "category", "level", "kind", "title", "description", "entry", "params",
                "returns", "types", "effects", "visible_examples", "notes"):
        if key not in task:
            errs.append("missing key %r" % key)
    if errs:
        return errs
    m = _TASK_ID.match(task["id"]) if isinstance(task["id"], str) else None
    if not m:
        errs.append("id must look like <category>_<NNN>, got %r" % (task["id"],))
    if task["category"] not in CATEGORIES:
        errs.append("category must be one of %s, got %r" % (list(CATEGORIES), task["category"]))
    elif m and not fixture and m.group(1) != task["category"]:
        errs.append("id prefix %r must equal the category %r" % (m.group(1), task["category"]))
    if isinstance(task["level"], bool) or task["level"] not in (1, 2, 3):
        errs.append("level must be 1, 2 or 3")
    if task["kind"] not in KINDS:
        errs.append("kind must be 'write' or 'edit'")
    for key in ("title", "description"):
        if not isinstance(task[key], str) or not task[key].strip():
            errs.append("%s must be a non-empty string" % key)
    if not isinstance(task["notes"], str):
        errs.append("notes must be a string")
    if not isinstance(task["entry"], str) or not _IDENT.match(task["entry"]):
        errs.append("entry must be a function name (snake_case), got %r" % (task["entry"],))

    # record types
    records: Dict[str, Any] = {}
    if not isinstance(task["types"], list):
        errs.append("types must be a list")
    else:
        for r in task["types"]:
            if (not isinstance(r, dict) or not isinstance(r.get("name"), str)
                    or not _TYPE_NAME.match(r["name"]) or r["name"] in _RESERVED
                    or not isinstance(r.get("fields"), list) or not r["fields"]):
                errs.append("bad record type declaration %r" % (r,))
                continue
            if r["name"] in records:
                errs.append("record type %s declared twice" % r["name"])
            records[r["name"]] = r
        for name, r in records.items():
            seen = set()
            for f in r["fields"]:
                if not isinstance(f, dict) or not isinstance(f.get("name"), str) or not _IDENT.match(f["name"]):
                    errs.append("record %s: bad field %r" % (name, f))
                    continue
                if f["name"] in seen:
                    errs.append("record %s: duplicate field %s" % (name, f["name"]))
                seen.add(f["name"])
                try:
                    parse_type(f.get("type", ""), records)
                except ValueError as ex:
                    errs.append("record %s field %s: %s" % (name, f["name"], ex))

    # signature
    params: List[Tuple[str, Type]] = []
    if not isinstance(task["params"], list):
        errs.append("params must be a list")
    else:
        seen_p = set()
        for p in task["params"]:
            if not isinstance(p, dict) or not isinstance(p.get("name"), str) or not _IDENT.match(p["name"]):
                errs.append("bad param %r" % (p,))
                continue
            if p["name"] in seen_p:
                errs.append("duplicate param %s" % p["name"])
            seen_p.add(p["name"])
            try:
                params.append((p["name"], parse_type(p.get("type", ""), records)))
            except ValueError as ex:
                errs.append("param %s: %s" % (p["name"], ex))
    ret: Optional[Type] = None
    try:
        ret = parse_type(task["returns"], records) if isinstance(task["returns"], str) else None
        if ret is None:
            errs.append("returns must be a type string")
    except ValueError as ex:
        errs.append("returns: %s" % ex)

    # effects
    if not isinstance(task["effects"], list) or any(e not in EFFECTS for e in task["effects"]):
        errs.append("effects must be [] or [\"console\"]")

    # visible examples
    ve = task["visible_examples"]
    if not isinstance(ve, list) or not 1 <= len(ve) <= 2:
        errs.append("visible_examples must hold 1 or 2 examples")
    elif not errs:
        recs = record_map(task)
        for i, ex in enumerate(ve):
            errs += ["visible_examples[%d]: %s" % (i, e) for e in _check_case(ex, params, ret, recs, False)]
    return errs


def _check_case(case: Any, params: List[Tuple[str, Type]], ret: Optional[Type],
                recs: Dict[str, Dict[str, Type]], with_stdout: bool) -> List[str]:
    if not isinstance(case, dict) or "args" not in case or "expect" not in case:
        return ["needs \"args\" and \"expect\""]
    if not isinstance(case["args"], list) or len(case["args"]) != len(params):
        return ["args must be a list of %d values" % len(params)]
    errs: List[str] = []
    for (name, t), a in zip(params, case["args"]):
        errs += check_value(a, t, recs, "args." + name)
    if ret is not None:
        errs += check_value(case["expect"], ret, recs, "expect")
    return errs


def validate_tests(task: Dict[str, Any], tests: Any) -> List[str]:
    """Errors for tests.json against its (already valid) task."""
    if not isinstance(tests, list):
        return ["tests.json must be a list"]
    errs: List[str] = []
    if len(tests) < MIN_TESTS:
        errs.append("need at least %d tests, got %d" % (MIN_TESTS, len(tests)))
    recs = record_map(task)
    params = [(p["name"], parse_type(p["type"], recs)) for p in task["params"]]
    ret = parse_type(task["returns"], recs)
    console = "console" in task["effects"]
    for i, case in enumerate(tests):
        errs += ["tests[%d]: %s" % (i, e) for e in _check_case(case, params, ret, recs, console)]
        if isinstance(case, dict):
            if console and not isinstance(case.get("stdout"), str):
                errs.append("tests[%d]: effects has console, so \"stdout\" (a string) is required" % i)
            if not console and "stdout" in case:
                errs.append("tests[%d]: \"stdout\" is only allowed when effects has console" % i)
    return errs


# ---------------------------------------------------------------------------
# Record validation (schema 1)
# ---------------------------------------------------------------------------

_ROUND_KEYS = {"i": int, "tool_ok": bool, "diag_codes": list, "unknown_names": int,
               "in_tokens": int, "out_tokens": int}


def _is(v: Any, typ: type) -> bool:
    if typ is int:
        return isinstance(v, int) and not isinstance(v, bool)
    return isinstance(v, typ)


def validate_record(rec: Any) -> List[str]:
    """Errors for one results record (empty list = valid)."""
    if not isinstance(rec, dict):
        return ["record must be an object"]
    spec = {"schema": int, "run_id": str, "set": str, "task_id": str, "category": str, "kind": str,
            "lang": str, "variant": str, "model": str, "repeat": int, "rounds": list,
            "first_try_pass": bool, "final_pass": bool, "final_tests": dict,
            "total_in_tokens": int, "total_out_tokens": int, "wall_ms": int}
    errs: List[str] = []
    for key, typ in spec.items():
        if key not in rec:
            errs.append("missing key %r" % key)
        elif not _is(rec[key], typ):
            errs.append("%s must be %s" % (key, typ.__name__))
    for key in ("temperature", "accepted_round", "error"):
        if key not in rec:
            errs.append("missing key %r" % key)
    if errs:
        return errs
    extra = set(rec) - set(spec) - {"temperature", "accepted_round", "error"}
    if extra:
        errs.append("unexpected keys %s" % sorted(extra))
    if rec["schema"] != RECORD_SCHEMA_VERSION:
        errs.append("schema must be %d" % RECORD_SCHEMA_VERSION)
    if rec["set"] not in ("dev", "hidden"):
        errs.append("set must be 'dev' or 'hidden'")
    if rec["category"] not in CATEGORIES:
        errs.append("bad category %r" % rec["category"])
    if rec["kind"] not in KINDS:
        errs.append("bad kind %r" % rec["kind"])
    if isinstance(rec["temperature"], bool) or not isinstance(rec["temperature"], (int, float)):
        errs.append("temperature must be a number")
    if rec["error"] is not None and not isinstance(rec["error"], str):
        errs.append("error must be a string or null")
    ar = rec["accepted_round"]
    if ar is not None and not (_is(ar, int) and 1 <= ar <= len(rec["rounds"])):
        errs.append("accepted_round must be null or a round number present in rounds")
    for n, r in enumerate(rec["rounds"]):
        if not isinstance(r, dict) or not (set(_ROUND_KEYS) <= set(r) <= set(_ROUND_KEYS) | {"diags"}):
            errs.append("rounds[%d] must have exactly the keys %s (and optionally 'diags')" % (n, sorted(_ROUND_KEYS)))
            continue
        if "diags" in r:
            ds = r["diags"]
            if not isinstance(ds, list) or not all(
                    isinstance(d, dict) and isinstance(d.get("code"), str) and isinstance(d.get("message"), str)
                    and (d.get("line") is None or _is(d.get("line"), int)) and set(d) == {"code", "line", "message"}
                    for d in ds):
                errs.append("rounds[%d].diags must be a list of {code, line, message}" % n)
        for key, typ in _ROUND_KEYS.items():
            if not _is(r[key], typ):
                errs.append("rounds[%d].%s must be %s" % (n, key, typ.__name__))
        if not isinstance(r["diag_codes"], list) or not all(isinstance(c, str) for c in r["diag_codes"]):
            errs.append("rounds[%d].diag_codes must be a list of strings" % n)
        if r["i"] != n + 1:
            errs.append("rounds[%d].i must be %d" % (n, n + 1))
    ft = rec["final_tests"]
    if (set(ft) != {"passed", "total"} or not _is(ft.get("passed"), int) or not _is(ft.get("total"), int)
            or ft["passed"] > ft["total"]):
        errs.append("final_tests must be {passed, total} with passed <= total")
    return errs


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _read_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as ex:
        raise TaskError("%s: %s" % (path, ex))


def load_task(task_dir: str, fixture: bool = False) -> Dict[str, Any]:
    """Load and validate one task directory. Returns the task dict plus
    `_dir`, `_tests` (list) keys. Raises TaskError."""
    task = _read_json(os.path.join(task_dir, "task.json"))
    errs = validate_task(task, fixture)
    if errs:
        raise TaskError("%s/task.json: %s" % (task_dir, "; ".join(errs)))
    tests = _read_json(os.path.join(task_dir, "tests.json"))
    errs = validate_tests(task, tests)
    if errs:
        raise TaskError("%s/tests.json: %s" % (task_dir, "; ".join(errs)))
    if os.path.basename(os.path.normpath(task_dir)) != task["id"]:
        raise TaskError("%s: directory name must equal the task id %r" % (task_dir, task["id"]))
    task = dict(task)
    task["_dir"] = task_dir
    task["_tests"] = tests
    return task


def find_task_dirs(root: str) -> List[Tuple[str, bool]]:
    """(directory, fixture) for every task under `root`. Accepts root/<category>/<task_id>/ and
    root/<task_id>/ (so a fixture folder can be used as a root). Names starting with `_` below the
    root are skipped; a root whose own name starts with `_`, or that lies under a folder named `experiments`, marks its tasks as
    fixtures (their id prefix need not equal a category)."""
    root = os.path.normpath(root)
    fixture = (os.path.basename(root).startswith("_")
               or "experiments" in root.replace("\\", "/").split("/"))
    found: List[Tuple[str, bool]] = []
    if not os.path.isdir(root):
        raise TaskError("tasks dir not found: %s" % root)
    for name in sorted(os.listdir(root)):
        if name.startswith("_"):
            continue
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        if os.path.exists(os.path.join(d, "task.json")):
            found.append((d, fixture))
            continue
        for sub in sorted(os.listdir(d)):
            sd = os.path.join(d, sub)
            if not sub.startswith("_") and os.path.isdir(sd) and os.path.exists(os.path.join(sd, "task.json")):
                found.append((sd, fixture))
    return found


def load_tasks(roots: List[str], only: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """All tasks under the given roots (sorted by id within a root), optionally filtered by id."""
    tasks: List[Dict[str, Any]] = []
    seen = set()
    for root in roots:
        for d, fixture in find_task_dirs(root):
            t = load_task(d, fixture)
            if only and t["id"] not in only:
                continue
            if t["id"] in seen:
                raise TaskError("duplicate task id %s" % t["id"])
            seen.add(t["id"])
            tasks.append(t)
    if only:
        missing = [i for i in only if i not in seen]
        if missing:
            raise TaskError("unknown task id(s): %s" % ", ".join(missing))
    return tasks
