"""Python adapter, plain: byte-compile, import, run the visible examples. No linter, no type checker."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from ..schema import parse_type, record_map
from .base import Adapter

TOOL_TIMEOUT = 60
RUN_TIMEOUT = 120

PRELUDE = '''\
"""Result type for benchmark programs (written next to your program as bench_prelude.py)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True)
class Err:
    message: str


Result = Union[Ok[T], Err]
'''

_RUNNER = r'''
import contextlib, dataclasses, io, json, os, sys, traceback

sys.dont_write_bytecode = True   # the workdir is reused across attempts: never trust a stale .pyc
sys.path.insert(0, os.getcwd())
mode, spec_path = sys.argv[1], sys.argv[2]
with open(spec_path, encoding="utf-8") as f:
    spec = json.load(f)
TYPES = spec["types"]


def where(tb):
    line = None
    for fr in traceback.extract_tb(tb):
        if os.path.basename(fr.filename) == "solution.py":
            line = fr.lineno
    return line


def err_of(ex):
    return {"type": type(ex).__name__, "message": str(ex)[:300],
            "line": getattr(ex, "lineno", None) or where(ex.__traceback__)}


def decode(v, t, mod, prelude):
    k = t[0]
    if k == "List":
        return [decode(x, t[1], mod, prelude) for x in v]
    if k == "Option":
        return None if v["$"] == "none" else decode(v["args"][0], t[1], mod, prelude)
    if k == "Result":
        if v["$"] == "ok":
            return prelude.Ok(decode(v["args"][0], t[1], mod, prelude))
        return prelude.Err(v["args"][0])
    if k == "Rec":
        cls = getattr(mod, t[1])
        return cls(**{f: decode(v[f], ft, mod, prelude) for f, ft in TYPES[t[1]].items()})
    return v


def encode(v, t, prelude):
    k = t[0]
    if k == "Int":
        if isinstance(v, bool) or not isinstance(v, int):
            raise TypeError("expected int, got %s" % type(v).__name__)
        return v
    if k == "Bool":
        if not isinstance(v, bool):
            raise TypeError("expected bool, got %s" % type(v).__name__)
        return v
    if k == "Text":
        if not isinstance(v, str):
            raise TypeError("expected str, got %s" % type(v).__name__)
        return v
    if k == "List":
        if not isinstance(v, (list, tuple)):
            raise TypeError("expected list, got %s" % type(v).__name__)
        return [encode(x, t[1], prelude) for x in v]
    if k == "Option":
        return {"$": "none"} if v is None else {"$": "some", "args": [encode(v, t[1], prelude)]}
    if k == "Result":
        if isinstance(v, prelude.Ok):
            return {"$": "ok", "args": [encode(v.value, t[1], prelude)]}
        if isinstance(v, prelude.Err):
            return {"$": "err", "args": [encode(v.message, t[2], prelude)]}
        raise TypeError("expected Ok or Err, got %s" % type(v).__name__)
    if k == "Rec":
        if type(v).__name__ != t[1] or not dataclasses.is_dataclass(v):
            raise TypeError("expected record %s, got %s" % (t[1], type(v).__name__))
        return {f: encode(getattr(v, f), ft, prelude) for f, ft in TYPES[t[1]].items()}
    raise TypeError("unsupported type")


out = {"stage": "ok", "error": None, "results": []}
sink = io.StringIO()
try:
    with open("solution.py", encoding="utf-8") as f:
        src = f.read()
    compile(src, "solution.py", "exec")
except SyntaxError as ex:
    out.update(stage="compile", error=err_of(ex))
    print(json.dumps(out)); sys.exit(0)
try:
    import bench_prelude as prelude
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(io.StringIO()):
        import solution as mod
except BaseException as ex:
    out.update(stage="import", error=err_of(ex))
    print(json.dumps(out)); sys.exit(0)
fn = getattr(mod, spec["entry"], None)
if not callable(fn):
    out.update(stage="entry", error={"type": "MissingEntry", "message": "no function named %r" % spec["entry"], "line": None})
    print(json.dumps(out)); sys.exit(0)
for case in spec["cases"]:
    res = {"got": None, "stdout": "", "error": None}
    buf = io.StringIO()
    try:
        args = [decode(a, t, mod, prelude) for a, t in zip(case["args"], spec["params"])]
        with contextlib.redirect_stdout(buf):
            value = fn(*args)
        res["got"] = encode(value, spec["returns"], prelude)
    except BaseException as ex:
        res["error"] = err_of(ex)
    res["stdout"] = buf.getvalue()
    out["results"].append(res)
print(json.dumps(out))
'''

_UNKNOWN_RUNTIME = ("NameError", "AttributeError", "UnboundLocalError")


def tool_command(name: str) -> Optional[List[str]]:
    """How to run an external Python tool as a program: its executable, else `python -m <name>`."""
    path = shutil.which(name)
    if path:
        return [path]
    if importlib.util.find_spec(name) is not None:
        return [sys.executable, "-m", name]
    return None


def python_primer() -> str:
    return """\
You write a Python 3.9+ program (standard library only). Reply with the complete program in one
fenced code block. Hidden tests import your module and call the requested function by name.

Value mapping (the task text uses Zehn type notation):
- Int -> int, Bool -> bool, Text -> str, List<T> -> list[T] (use typing.List[T] on Python 3.9)
- Option<T> -> Optional[T]: None for none, the plain value for some
- Result<T, Text> -> from bench_prelude import Ok, Err, Result: Ok(value) / Err(message);
  annotate as Result[T]
- A record type -> a @dataclass with exactly the declared field names; you declare it yourself
- Console effect: use print(); the tests compare the exact text printed

bench_prelude.py (it sits next to your program; do not redefine it):

```python
""" + PRELUDE + """```

Your program is checked by the tool described below; its diagnostics come back to you if it fails.
"""


class PythonPlainAdapter(Adapter):
    name = "python_plain"
    ext = ".py"
    external_tools: List[str] = []
    strict = False

    def available(self) -> Tuple[bool, str]:
        return True, ""

    def tool_command(self, name: str) -> Optional[List[str]]:
        return tool_command(name)

    def system_prompt(self, task: Dict[str, Any]) -> str:
        return python_primer() + (
            "Checks: the program is byte-compiled, imported, and the visible examples are run.\n")

    # -- helpers --------------------------------------------------------------------------------
    def _prepare(self, task: Dict[str, Any], code: str, cases: List[Dict[str, Any]], workdir: str) -> str:
        with open(os.path.join(workdir, "solution.py"), "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        with open(os.path.join(workdir, "bench_prelude.py"), "w", encoding="utf-8", newline="\n") as f:
            f.write(PRELUDE)
        with open(os.path.join(workdir, "_bench_runner.py"), "w", encoding="utf-8", newline="\n") as f:
            f.write(_RUNNER)
        recs = record_map(task)
        types = {n: {f: list(_tree(t)) for f, t in fs.items()} for n, fs in recs.items()}
        names = {r["name"]: r for r in task["types"]}
        spec = {"entry": task["entry"],
                "params": [_tree(parse_type(p["type"], names)) for p in task["params"]],
                "returns": _tree(parse_type(task["returns"], names)),
                "types": types, "cases": cases}
        path = os.path.join(workdir, "_bench_spec.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f)
        return path

    def _run(self, spec_path: str, mode: str, workdir: str) -> Optional[Dict[str, Any]]:
        try:
            p = subprocess.run([sys.executable, "_bench_runner.py", mode, spec_path], cwd=workdir,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                               timeout=RUN_TIMEOUT)
            return json.loads(p.stdout)
        except (subprocess.TimeoutExpired, ValueError):
            return None

    @staticmethod
    def _same(case: Dict[str, Any], res: Dict[str, Any], console: bool) -> bool:
        if res["error"] is not None:
            return False
        if json.dumps(res["got"], sort_keys=True) != json.dumps(case["expect"], sort_keys=True):
            return False
        return not (console and "stdout" in case and res["stdout"] != case["stdout"])

    @staticmethod
    def _d(code: str, message: str, line: Optional[int], unknown: bool = False, raw: str = "") -> Dict[str, Any]:
        return {"code": code, "message": message, "line": line, "unknown_name": unknown, "raw": raw or message}

    # -- contract -------------------------------------------------------------------------------
    def tool_check(self, task: Dict[str, Any], code: str, workdir: str) -> Dict[str, Any]:
        t0 = time.time()
        cases = [{"args": e["args"], "expect": e["expect"]} for e in task["visible_examples"]]
        spec_path = self._prepare(task, code, cases, workdir)
        diags: List[Dict[str, Any]] = []
        data = self._run(spec_path, "check", workdir)
        stage = "timeout"
        if data is None:
            diags.append(self._d("TOOL_TIMEOUT", "the program did not finish in %ds" % RUN_TIMEOUT, None))
        else:
            stage = data["stage"]
            if stage != "ok":
                e = data["error"]
                name = e["type"]
                diags.append(self._d(name, e["message"], e["line"], name in _UNKNOWN_RUNTIME, json.dumps(e)))
            else:
                for i, (case, res) in enumerate(zip(cases, data["results"])):
                    if res["error"] is not None:
                        e = res["error"]
                        diags.append(self._d(e["type"], "example %d raised %s: %s" % (i, e["type"], e["message"]),
                                             e["line"], e["type"] in _UNKNOWN_RUNTIME, json.dumps(e)))
                    elif not self._same(case, res, False):
                        diags.append(self._d("ExampleFail", "example %d: got %s, expected %s" % (
                            i, json.dumps(res["got"]), json.dumps(case["expect"])), None))
        if self.strict and stage != "compile":
            diags += self._strict_diags(workdir)
        ok = not diags
        return {"ok": ok, "diagnostics": diags, "tool_ms": int((time.time() - t0) * 1000)}

    def _strict_diags(self, workdir: str) -> List[Dict[str, Any]]:
        return []

    def run_hidden(self, task: Dict[str, Any], code: str, tests: List[Dict[str, Any]],
                   workdir: str) -> Dict[str, Any]:
        t0 = time.time()
        total = len(tests)
        spec_path = self._prepare(task, code, tests, workdir)
        data = self._run(spec_path, "hidden", workdir)
        ms = lambda: int((time.time() - t0) * 1000)  # noqa: E731
        if data is None:
            return {"passed": 0, "total": total, "failures": [], "ms": ms()}
        if data["stage"] != "ok":
            return {"passed": 0, "total": total, "ms": ms(),
                    "failures": [{"index": -1, "got": json.dumps(data["error"]), "want": data["stage"]}]}
        console = "console" in task["effects"]
        passed, failures = 0, []
        for i, (case, res) in enumerate(zip(tests, data["results"])):
            if self._same(case, res, console):
                passed += 1
            else:
                got = json.dumps(res["error"]) if res["error"] else json.dumps(res["got"])
                failures.append({"index": i, "got": got[:300], "want": json.dumps(case["expect"])[:300]})
        return {"passed": passed, "total": total, "failures": failures, "ms": ms()}


def _tree(t: Tuple[Any, ...]) -> List[Any]:
    """Parsed type -> JSON-able nested list."""
    return [t[0]] + [(_tree(x) if isinstance(x, tuple) else x) for x in t[1:]]
