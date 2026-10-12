"""Strict TypeScript adapter: `tsc` with strict, noImplicitReturns, noUncheckedIndexedAccess and
noFallthroughCasesInSwitch, then `node` runs the compiled program. Stdlib only, Python 3.9+.

No package.json and no node_modules: `tsc` and `node` come from PATH. The model's program is
`prog.ts` (its own text first), followed by `export {};` (so it is always a module) and a generated
harness that calls `entry` and prints one JSON line per test between marker characters. `console` is
declared by an ambient file (`bench_env.d.ts`), so no @types/node is needed. Int = `number`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import rust as _rust
from .base import Adapter

LANGS_DIR = Path(__file__).resolve().parents[2] / "langs" / "ts"
UNKNOWN_NAME_CODES = frozenset(["TS2304", "TS2339"])
MAX_SAFE_INT = 2 ** 53 - 1

_TSC_RE = re.compile(r"^(?P<file>[^\s(][^()]*)\((?P<line>\d+),(?P<col>\d+)\): (?:error|warning) "
                     r"(?P<code>TS\d+): (?P<msg>.*)$")
_TSC_NOFILE_RE = re.compile(r"^(?:error|warning) (?P<code>TS\d+): (?P<msg>.*)$")


# ---------------------------------------------------------------- types and values

def _ts_type(t: tuple, ro: bool = False) -> str:
    k = t[0]
    if k == "Int":
        return "number"
    if k == "Bool":
        return "boolean"
    if k == "Text":
        return "string"
    if k == "Unit":
        return "void"
    if k == "List":
        el = _ts_type(t[1], ro)
        if t[1][0] in ("Option", "Result"):
            el = "(%s)" % el
        return ("readonly " if ro else "") + el + "[]"
    if k == "Option":
        return "%s | null" % _ts_type(t[1], ro)
    if k == "Result":
        return "{ ok: true; value: %s } | { ok: false; error: string }" % _ts_type(t[1], ro)
    return t[1]


def _ts_lit(env: _rust._TypeEnv, t: tuple, v: Any) -> str:
    """TypeScript expression for a JSON test value of type `t` (also validates it)."""
    k = t[0]
    if k == "Int":
        n = _rust._check_int(v)
        if abs(n) > MAX_SAFE_INT:
            raise ValueError("Int %d is outside +-2^53-1; TypeScript Int is `number`" % n)
        return "(%d)" % n if n < 0 else str(n)
    if k == "Bool":
        _rust.canon(env, t, v)
        return "true" if v else "false"
    if k == "Text":
        return json.dumps(_rust._check_ascii(v))
    if k == "Unit":
        _rust.canon(env, t, v)
        return "undefined"
    if k == "List":
        if not isinstance(v, list):
            raise ValueError("expected a List, got %r" % (v,))
        return "[" + ", ".join(_ts_lit(env, t[1], x) for x in v) + "]"
    if k == "Option":
        tag, args = _rust._tagged(v, ("some", "none"))
        return "null" if tag == "none" else _ts_lit(env, t[1], args[0])
    if k == "Result":
        tag, args = _rust._tagged(v, ("ok", "err"))
        if tag == "ok":
            return "{ ok: true, value: %s }" % _ts_lit(env, t[1], args[0])
        return "{ ok: false, error: %s }" % json.dumps(_rust._check_ascii(args[0]))
    _rust.canon(env, t, v)
    fields = env.records[t[1]]
    return "{ " + ", ".join("%s: %s" % (json.dumps(n), _ts_lit(env, ft, v[n])) for n, ft in fields) + " }"


class _Printers:
    """Generates one `function __benchJsN(v: T): string` per distinct type; the result is canonical JSON text."""

    def __init__(self, env: _rust._TypeEnv) -> None:
        self.env = env
        self.names = {}  # type: Dict[tuple, str]
        self.defs = []  # type: List[str]

    def printer(self, t: tuple) -> str:
        if t in self.names:
            return self.names[t]
        name = "__benchJs%d" % len(self.names)
        self.names[t] = name
        k = t[0]
        sig = "function %s(v: %s): string {" % (name, _ts_type(t, ro=True))
        if k in ("Int", "Bool", "Text"):
            body = ["  return JSON.stringify(v);"]
        elif k == "Unit":
            body = ['  return "null";']
        elif k == "List":
            body = ['  return "[" + v.map(%s).join(",") + "]";' % self.printer(t[1])]
        elif k == "Option":
            body = ["  if (v === null) {", "    return '{\"$\":\"none\"}';", "  }",
                    "  return '{\"$\":\"some\",\"args\":[' + %s(v) + ']}';" % self.printer(t[1])]
        elif k == "Result":
            body = ["  if (v.ok) {",
                    "    return '{\"$\":\"ok\",\"args\":[' + %s(v.value) + ']}';" % self.printer(t[1]),
                    "  }",
                    "  return '{\"$\":\"err\",\"args\":[' + JSON.stringify(v.error) + ']}';"]
        else:
            parts = ["'{'"]
            for i, (fname, ft) in enumerate(self.env.records[t[1]]):
                parts.append(("',' + " if i else "") + "JSON.stringify(%s) + ':' + %s(v.%s)"
                             % (json.dumps(fname), self.printer(ft), fname))
            parts.append("'}'")
            body = ["  return " + " + ".join(parts) + ";"]
        self.defs.append("\n".join([sig] + body + ["}"]))
        return name


# ---------------------------------------------------------------- diagnostics

def parse_tsc(stdout: str, nuser: int) -> List[Dict[str, Any]]:
    """Diagnostics from `tsc --pretty false` output (continuation lines go to `raw`)."""
    diags = []  # type: List[Dict[str, Any]]
    for ln in stdout.splitlines():
        m = _TSC_RE.match(ln)
        if m:
            code, msg = m.group("code"), m.group("msg")
            line = int(m.group("line"))
            in_harness = line > nuser
            if in_harness:
                msg = "(entry point check against the task signature) " + msg
            user_line = None if in_harness else line
            diags.append(_rust._diag(code, msg, user_line, ln, unknown_name=(code in UNKNOWN_NAME_CODES and not in_harness)))
            continue
        m = _TSC_NOFILE_RE.match(ln)
        if m:
            diags.append(_rust._diag(m.group("code"), m.group("msg"), None, ln))
        elif diags and ln.strip():
            diags[-1]["raw"] += "\n" + ln
    return diags


# ---------------------------------------------------------------- the adapter

class TsStrictAdapter(Adapter):
    name = "ts_strict"
    ext = ".ts"
    build_timeout = 120.0   # seconds for tsc
    run_timeout = 10.0      # seconds for node

    def available(self) -> Tuple[bool, str]:
        missing = [t for t in ("tsc", "node") if shutil.which(t) is None]
        if missing:
            return False, "%s not found on PATH (install commands: bench/langs/README.md)" % ", ".join(missing)
        return True, ""

    def system_prompt(self, task: Dict[str, Any]) -> str:
        env = _rust._TypeEnv(task)
        params = ", ".join("%s: %s" % (p["name"], _ts_type(env.parse(p["type"]))) for p in task["params"])
        lines = [
            "You write TypeScript, compiled by `tsc` with strict, noImplicitReturns, noUncheckedIndexedAccess",
            "and noFallthroughCasesInSwitch (target ES2020, no Node typings, no imports).",
            "Reply with the complete source of one file. A test harness is appended to it and calls your",
            "function `%s`; do not call it yourself." % task["entry"],
            "Value mapping: Int = number, Bool = boolean, Text = string, List<T> = T[],",
            "Option<T> = T | null, Result<T, Text> = { ok: true, value: T } | { ok: false, error: string }.",
            "Declare the record types yourself as interfaces or type aliases, with exactly the field names given.",
            "Required signature:",
            "    function %s(%s): %s" % (task["entry"], params, _ts_type(env.parse(task["returns"]))),
        ]
        for name, fields in env.records.items():
            lines.append("Record `%s`: %s" % (name, ", ".join("%s: %s" % (n, _ts_type(ft)) for n, ft in fields)))
        if "console" in (task.get("effects") or []):
            lines.append("Console output: use `console.log`; the exact text printed is part of the result.")
        lines.append("The feedback tool runs `tsc` and returns the compiler errors with line numbers.")
        return "\n".join(lines)

    # -- project generation

    def _harness(self, task: Dict[str, Any], env: _rust._TypeEnv,
                 tests: Optional[List[Dict[str, Any]]]) -> str:
        ptypes = [env.parse(p["type"]) for p in task["params"]]
        rtype = env.parse(task["returns"])
        pr = _Printers(env)
        top = pr.printer(rtype)
        entry = task["entry"]
        out = []  # type: List[str]
        if tests is None:
            sig = ", ".join("a%d: %s" % (i, _ts_type(t)) for i, t in enumerate(ptypes))
            out.append("const __benchSig: (%s) => %s = %s;" % (sig, _ts_type(rtype, ro=True), entry))
        else:
            out.append("function __benchRun(): void {")
            for i, test in enumerate(tests):
                args = test["args"]
                if len(args) != len(ptypes):
                    raise ValueError("test %d has %d args, the task has %d params" % (i, len(args), len(ptypes)))
                call = "%s(%s)" % (entry, ", ".join(_ts_lit(env, t, a) for t, a in zip(ptypes, args)))
                out.append('  console.log("\\u0001B%d\\u0002");' % i)
                out.append("  const r%d = %s;" % (i, call))
                out.append('  console.log("\\u0001E%d\\u0002" + %s(r%d) + "\\u0003");' % (i, top, i))
            out.append("}")
            out.append("__benchRun();")
        return "\n\n".join(pr.defs) + "\n\n" + "\n".join(out) + "\n"

    def _prepare(self, task: Dict[str, Any], code: str, tests: Optional[List[Dict[str, Any]]],
                 workdir: str) -> Tuple[str, int]:
        env = _rust._TypeEnv(task)
        proj = os.path.join(workdir, self.name)
        os.makedirs(proj, exist_ok=True)
        for tmpl, target in (("tsconfig.json.tmpl", "tsconfig.json"), ("bench_env.d.ts.tmpl", "bench_env.d.ts")):
            with open(os.path.join(proj, target), "w", encoding="utf-8", newline="\n") as f:
                f.write((LANGS_DIR / tmpl).read_text(encoding="utf-8"))
        user = code.replace("\r\n", "\n").rstrip("\n")
        nuser = user.count("\n") + 1 if user else 0
        text = (user + "\n\n" if user else "") + "export {};\n\n" + self._harness(task, env, tests)
        with open(os.path.join(proj, "prog.ts"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return proj, nuser

    def _compile(self, proj: str, nuser: int) -> Tuple[bool, List[Dict[str, Any]]]:
        shutil.rmtree(os.path.join(proj, "out"), ignore_errors=True)
        tsc = shutil.which("tsc") or "tsc"
        rc, out, err, timed_out = _rust._run([tsc, "-p", "tsconfig.json", "--pretty", "false"], proj,
                                             dict(os.environ), self.build_timeout)
        diags = parse_tsc(out, nuser)
        if timed_out:
            diags.append(_rust._diag("tsc", "tsc timed out after %d s" % self.build_timeout, None, err[-2000:]))
        elif rc != 0 and not diags:
            first = next((x for x in (err + out).splitlines() if x.strip()), "tsc failed (exit %d)" % rc)
            diags.append(_rust._diag("tsc", first.strip(), None, (err + out)[-4000:]))
        return (rc == 0 and not timed_out), diags

    # -- contract

    def tool_check(self, task: Dict[str, Any], code: str, workdir: str) -> Dict[str, Any]:
        t0 = time.monotonic()
        proj, nuser = self._prepare(task, code, None, workdir)
        ok, diags = self._compile(proj, nuser)
        return {"ok": ok, "diagnostics": diags, "tool_ms": _rust._ms(t0)}

    def run_hidden(self, task: Dict[str, Any], code: str, tests: List[Dict[str, Any]],
                   workdir: str) -> Dict[str, Any]:
        t0 = time.monotonic()
        env = _rust._TypeEnv(task)
        rtype = env.parse(task["returns"])
        wants = [_rust.canon(env, rtype, t["expect"]) for t in tests]
        proj, nuser = self._prepare(task, code, tests, workdir)
        ok, diags = self._compile(proj, nuser)
        if not ok:
            first = diags[0]["message"] if diags else "build failed"
            return _rust._failed(len(tests), "build failed: " + first, wants, t0)
        node = shutil.which("node") or "node"
        rc, out, err, timed_out = _rust._run([node, "out/prog.js"], proj, dict(os.environ), self.run_timeout)
        if timed_out:
            return _rust._failed(len(tests), "timed out after %g s" % self.run_timeout, wants, t0)
        if rc != 0:
            return _rust._failed(len(tests), "crashed (exit %d): %s" % (rc, _rust.crash_summary(err)), wants, t0)
        return _rust._score(tests, wants, out, "\n", t0)
