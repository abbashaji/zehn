"""Rust adapter: plain `cargo build` of a generated crate (edition 2021, no external crates).

The model's program is `src/main.rs` (its own text first, byte for byte), followed by a generated
harness module and a `fn main`. The harness is a child module of the crate root, so it can reach
private items of the model's code (`use super::*`). It prints one JSON line per test between marker
characters, so the program's own stdout can be separated from the result. Stdlib only, Python 3.9+.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import Adapter

LANGS_DIR = Path(__file__).resolve().parents[2] / "langs" / "rust"
UNKNOWN_NAME_CODES = frozenset(["E0425", "E0433", "E0412", "E0599"])
INT_MIN = -(2 ** 63)
INT_MAX = 2 ** 63 - 1
_RS_KEYWORDS = frozenset((
    "as break const continue crate else enum extern false fn for if impl in let loop match mod move "
    "mut pub ref return self Self static struct super trait true type unsafe use where while async "
    "await dyn abstract become box do final macro override priv typeof unsized virtual yield try"
).split())

# markers around each test result in the program's stdout: \x01B<i>\x02 ... \x01E<i>\x02<json>\x03
_MARKER_RE = re.compile("\x01B(\\d+)\x02(.*?)\x01E(\\d+)\x02(.*?)\x03", re.S)
_ANSI_RE = re.compile("\x1b\\[[0-9;]*[A-Za-z]|\x0f")
_DIFF_RE = re.compile(r"^Diff in (.+?)(?: at line |:)(\d+):?\s*$")


# ---------------------------------------------------------------- types and values

class _TypeEnv:
    """Parses Zehn type syntax from task.json into small tuples: ("Int",), ("List", t), ("Record", name)."""

    def __init__(self, task: Dict[str, Any]) -> None:
        decls = task.get("types") or []
        self.names = set(r["name"] for r in decls)
        self.records = {}  # type: Dict[str, List[Tuple[str, tuple]]]
        for r in decls:
            self.records[r["name"]] = [(f["name"], self.parse(f["type"])) for f in r["fields"]]

    def parse(self, text: str) -> tuple:
        s = text.strip()
        if s in ("Int", "Bool", "Text", "Unit"):
            return (s,)
        m = re.match(r"^(List|Option|Result)<(.*)>$", s, re.S)
        if m:
            kind = m.group(1)
            parts = _split_top(m.group(2))
            if kind == "Result":
                if len(parts) != 2 or parts[1] != "Text":
                    raise ValueError("Result must be Result<T, Text>, got %r" % text)
                return ("Result", self.parse(parts[0]))
            if len(parts) != 1:
                raise ValueError("bad type %r" % text)
            inner = self.parse(parts[0])
            if kind == "Option" and inner[0] == "Option":
                raise ValueError("nested Option is not allowed: %r" % text)
            return (kind, inner)
        if s in self.names:
            return ("Record", s)
        raise ValueError("unknown type %r" % text)


def _split_top(s: str) -> List[str]:
    depth = 0
    parts = []  # type: List[str]
    cur = []  # type: List[str]
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts]


def _check_int(v: Any) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError("expected an Int, got %r" % (v,))
    if not INT_MIN <= v <= INT_MAX:
        raise ValueError("Int %d does not fit signed 64-bit" % v)
    return v


def _check_ascii(v: Any) -> str:
    if not isinstance(v, str):
        raise ValueError("expected a Text, got %r" % (v,))
    if any(ord(c) > 127 for c in v):
        raise ValueError("Text must be ASCII: %r" % (v,))
    return v


def _tagged(v: Any, tags: Tuple[str, ...]) -> Tuple[str, List[Any]]:
    if not isinstance(v, dict) or v.get("$") not in tags:
        raise ValueError("expected a value tagged with one of %s, got %r" % (list(tags), v))
    args = v.get("args", [])
    if not isinstance(args, list):
        raise ValueError("bad args in %r" % (v,))
    return v["$"], args


def canon(env: _TypeEnv, t: tuple, v: Any) -> str:
    """Canonical compact JSON text of value `v` of type `t` (declared field order). Raises ValueError."""
    k = t[0]
    if k == "Int":
        return str(_check_int(v))
    if k == "Bool":
        if not isinstance(v, bool):
            raise ValueError("expected a Bool, got %r" % (v,))
        return "true" if v else "false"
    if k == "Text":
        return json.dumps(_check_ascii(v))
    if k == "Unit":
        if v is not None:
            raise ValueError("expected null for Unit, got %r" % (v,))
        return "null"
    if k == "List":
        if not isinstance(v, list):
            raise ValueError("expected a List, got %r" % (v,))
        return "[" + ",".join(canon(env, t[1], x) for x in v) + "]"
    if k == "Option":
        tag, args = _tagged(v, ("some", "none"))
        if tag == "none":
            return '{"$":"none"}'
        if len(args) != 1:
            raise ValueError("some needs one arg: %r" % (v,))
        return '{"$":"some","args":[' + canon(env, t[1], args[0]) + "]}"
    if k == "Result":
        tag, args = _tagged(v, ("ok", "err"))
        if len(args) != 1:
            raise ValueError("%s needs one arg: %r" % (tag, v))
        if tag == "ok":
            return '{"$":"ok","args":[' + canon(env, t[1], args[0]) + "]}"
        return '{"$":"err","args":[' + json.dumps(_check_ascii(args[0])) + "]}"
    fields = env.records[t[1]]
    if not isinstance(v, dict) or sorted(v) != sorted(n for n, _ in fields):
        raise ValueError("record %s needs exactly the fields %s, got %r" % (t[1], [n for n, _ in fields], v))
    return "{" + ",".join(json.dumps(n) + ":" + canon(env, ft, v[n]) for n, ft in fields) + "}"


def _rs_ident(name: str) -> str:
    return "r#" + name if name in _RS_KEYWORDS else name


def _rs_type(t: tuple, short: bool = False) -> str:
    """Rust type text; `short` gives the idiomatic form shown to the model, else the fully qualified harness form."""
    k = t[0]
    if k in ("Int", "Bool", "Unit"):
        return {"Int": "i64", "Bool": "bool", "Unit": "()"}[k]
    if k == "Record":
        return t[1]
    string = "String" if short else "::std::string::String"
    if k == "Text":
        return string
    inner = _rs_type(t[1], short)
    if k == "List":
        return "%s<%s>" % ("Vec" if short else "::std::vec::Vec", inner)
    if k == "Option":
        return "%s<%s>" % ("Option" if short else "::std::option::Option", inner)
    return "%s<%s, %s>" % ("Result" if short else "::std::result::Result", inner, string)


def _rs_text(s: str) -> str:
    out = []
    for c in s:
        if c == '"':
            out.append('\\"')
        elif c == "\\":
            out.append("\\\\")
        elif c == "\n":
            out.append("\\n")
        elif c == "\r":
            out.append("\\r")
        elif c == "\t":
            out.append("\\t")
        elif ord(c) < 32 or ord(c) == 127:
            out.append("\\u{%x}" % ord(c))
        else:
            out.append(c)
    return '::std::string::String::from("' + "".join(out) + '")'


def _rs_lit(env: _TypeEnv, t: tuple, v: Any) -> str:
    """Rust expression for a JSON test value of type `t` (also validates it)."""
    k = t[0]
    if k == "Int":
        return "%di64" % _check_int(v)
    if k == "Bool":
        canon(env, t, v)
        return "true" if v else "false"
    if k == "Text":
        return _rs_text(_check_ascii(v))
    if k == "Unit":
        canon(env, t, v)
        return "()"
    if k == "List":
        if not isinstance(v, list):
            raise ValueError("expected a List, got %r" % (v,))
        if not v:
            return "::std::vec::Vec::<%s>::new()" % _rs_type(t[1])
        return "::std::vec![" + ", ".join(_rs_lit(env, t[1], x) for x in v) + "]"
    if k == "Option":
        tag, args = _tagged(v, ("some", "none"))
        if tag == "none":
            return "::std::option::Option::<%s>::None" % _rs_type(t[1])
        return "::std::option::Option::Some(%s)" % _rs_lit(env, t[1], args[0])
    if k == "Result":
        tag, args = _tagged(v, ("ok", "err"))
        head = "::std::result::Result::<%s, ::std::string::String>::" % _rs_type(t[1])
        if tag == "ok":
            return head + "Ok(%s)" % _rs_lit(env, t[1], args[0])
        return head + "Err(%s)" % _rs_text(_check_ascii(args[0]))
    canon(env, t, v)
    fields = env.records[t[1]]
    return "%s { %s }" % (t[1], ", ".join("%s: %s" % (_rs_ident(n), _rs_lit(env, ft, v[n])) for n, ft in fields))


# ---------------------------------------------------------------- processes

def _run(cmd: List[str], cwd: str, env: Dict[str, str], timeout: float) -> Tuple[int, str, str, bool]:
    """Run a program; returns (returncode, stdout, stderr, timed_out). The whole process group is killed on timeout."""
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except OSError as exc:
        return 127, "", "cannot start %s: %s" % (cmd[0], exc), False
    try:
        out, err = proc.communicate(timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (OSError, AttributeError):
            proc.kill()
        out, err = proc.communicate()
        timed_out = True
    return proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), timed_out


def _cargo_env() -> Dict[str, str]:
    env = dict(os.environ)
    env.update({"CARGO_TERM_COLOR": "never", "CARGO_INCREMENTAL": "0", "CARGO_NET_OFFLINE": "true",
                "RUST_BACKTRACE": "0", "NO_COLOR": "1"})
    return env


def crash_summary(err: str) -> str:
    """One short line about why a program died: the panic or uncaught error line, else the last stderr lines."""
    lines = [x.strip() for x in err.splitlines() if x.strip()]
    for i, ln in enumerate(lines):
        if "panicked at" in ln:
            return " ".join(lines[i:i + 2])
        if re.match(r"^(Uncaught )?\w*Error\b", ln):
            return ln
    return " ".join(lines[-2:])


def _ms(t0: float) -> int:
    return int(round((time.monotonic() - t0) * 1000))


# ---------------------------------------------------------------- diagnostics

def _diag(code: str, message: str, line: Optional[int], raw: str, unknown_name: bool = False) -> Dict[str, Any]:
    return {"code": code, "message": message, "line": line, "unknown_name": unknown_name, "raw": raw}


def _locate(spans: List[Dict[str, Any]], nuser: int) -> Tuple[Optional[int], bool]:
    """(line in the model's code or None, True if the error is in the generated harness part of main.rs)."""
    in_harness = False
    for s in sorted(spans, key=lambda x: not x.get("is_primary")):
        cur = s  # type: Optional[Dict[str, Any]]
        while cur:
            if str(cur.get("file_name", "")).replace("\\", "/").endswith("src/main.rs"):
                ln = cur.get("line_start")
                if isinstance(ln, int) and 1 <= ln <= nuser:
                    return ln, False
                in_harness = True
                break
            exp = cur.get("expansion")
            cur = exp.get("span") if exp else None
    return None, in_harness


def parse_cargo_json(stdout: str, nuser: int) -> List[Dict[str, Any]]:
    """Error-level compiler messages (rustc, and clippy lints promoted by -D warnings) from cargo's JSON stream."""
    diags = []  # type: List[Dict[str, Any]]
    for ln in stdout.splitlines():
        ln = ln.strip()
        if not ln.startswith("{"):
            continue
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        if rec.get("reason") != "compiler-message":
            continue
        m = rec.get("message") or {}
        if m.get("level") not in ("error", "error: internal compiler error"):
            continue
        text = str(m.get("message", ""))
        spans = m.get("spans") or []
        if not spans and (text.startswith("aborting due to") or text.startswith("could not compile")):
            continue
        code = (m.get("code") or {}).get("code") or ""
        line, in_harness = _locate(spans, nuser)
        if in_harness:
            detail = [str(sp.get("label")) for sp in spans if sp.get("is_primary") and sp.get("label")]
            detail += [str(c.get("message", "")) for c in (m.get("children") or [])
                       if c.get("level") == "note" and str(c.get("message", "")).startswith("expected")]
            detail_text = " ".join(" ".join(detail).split())
            text = "(entry point check against the task signature) " + text + (" [%s]" % detail_text if detail else "")
        diags.append(_diag(code, text, line, str(m.get("rendered") or text),
                           unknown_name=(code in UNKNOWN_NAME_CODES and line is not None)))
    return diags


def parse_fmt_diff(stdout: str, nuser: int) -> List[Dict[str, Any]]:
    """One diagnostic per `cargo fmt --check` hunk in src/main.rs (code "fmt")."""
    hunks = []  # type: List[Tuple[int, List[str]]]
    for ln in _ANSI_RE.sub("", stdout).splitlines():
        m = _DIFF_RE.match(ln)
        if m:
            hunks.append((int(m.group(2)) if m.group(1).replace("\\", "/").endswith("src/main.rs") else -1, []))
        elif hunks:
            hunks[-1][1].append(ln)
    diags = []  # type: List[Dict[str, Any]]
    for start, body in hunks:
        if start < 0:
            continue
        line = start
        for b in body:
            if b.startswith("-") or b.startswith("+"):
                break
            line += 1
        want = next((b[1:].strip() for b in body if b.startswith("+")), "")
        msg = "not formatted as rustfmt would (cargo fmt --check)"
        msg += "; expected: %s" % want if want else "; remove this line"
        diags.append(_diag("fmt", msg, line if line <= nuser else None, "\n".join(body)))
    return diags


# ---------------------------------------------------------------- the adapter

class RustAdapter(Adapter):
    name = "rust"
    ext = ".rs"
    needs = ("cargo", "rustc")
    build_timeout = 240.0   # seconds for one cargo invocation
    run_timeout = 10.0      # seconds for the compiled test program

    def available(self) -> Tuple[bool, str]:
        missing = [t for t in self.needs if shutil.which(t) is None]
        if missing:
            return False, "%s not found on PATH (install commands: bench/langs/README.md)" % ", ".join(missing)
        return True, ""

    # -- prompt

    def system_prompt(self, task: Dict[str, Any]) -> str:
        env = _TypeEnv(task)
        lines = [
            "You write Rust (edition 2021, standard library only, no external crates).",
            "Reply with the complete source of one file. It is compiled as the crate root `src/main.rs`.",
            "Do not write `fn main`; a test harness calls your function `%s` and prints its result." % task["entry"],
            "Value mapping: Int = i64, Bool = bool, Text = String, List<T> = Vec<T>, Option<T> = Option<T>,",
            "Result<T, Text> = Result<T, String>. All parameters are owned values (no references).",
            "Declare the record types yourself, with exactly the field names given; the field types are as above.",
            "Required signature:",
            "    " + self._signature(task, env),
        ]
        for name, fields in env.records.items():
            lines.append("Record `%s`: %s" % (name, ", ".join("%s: %s" % (n, _rs_type(ft, True)) for n, ft in fields)))
        if "console" in (task.get("effects") or []):
            lines.append("Console output: use `println!` / `print!`; the exact text printed is part of the result.")
        lines.append(self._tool_note())
        return "\n".join(lines)

    def _tool_note(self) -> str:
        return ("The feedback tool runs `cargo build`; it returns the compiler errors with line numbers "
                "(warnings are not reported).")

    @staticmethod
    def _signature(task: Dict[str, Any], env: _TypeEnv) -> str:
        params = ", ".join("%s: %s" % (p["name"], _rs_type(env.parse(p["type"]), True)) for p in task["params"])
        return "fn %s(%s) -> %s" % (task["entry"], params, _rs_type(env.parse(task["returns"]), True))

    # -- crate generation

    def _harness(self, task: Dict[str, Any], env: _TypeEnv, tests: Optional[List[Dict[str, Any]]]) -> str:
        ptypes = [env.parse(p["type"]) for p in task["params"]]
        rtype = env.parse(task["returns"])
        out = ["#[allow(dead_code, unused, clippy::all)]", "#[rustfmt::skip]", "mod bench_harness {",
               "use super::*;", "", (LANGS_DIR / "harness_prelude.rs.tmpl").read_text(encoding="utf-8")]
        for name, fields in env.records.items():
            out.append("impl BenchJs for %s {" % name)
            out.append("    fn bench_js(&self) -> ::std::string::String {")
            out.append("        let mut s = ::std::string::String::from(\"{\");")
            for i, (fname, _ft) in enumerate(fields):
                out.append("        s.push_str(%s);" % json.dumps(("," if i else "") + json.dumps(fname) + ":"))
                out.append("        s.push_str(&self.%s.bench_js());" % _rs_ident(fname))
            out.append("        s.push('}');")
            out.append("        s")
            out.append("    }")
            out.append("}")
            out.append("")
        out.append("pub fn run() {")
        entry = "super::" + task["entry"]
        if tests is None:
            out.append("    let _sig: fn(%s) -> %s = %s;" % (", ".join(_rs_type(t) for t in ptypes), _rs_type(rtype), entry))
        else:
            out.append("    use ::std::io::Write;")
            for i, test in enumerate(tests):
                args = test["args"]
                if len(args) != len(ptypes):
                    raise ValueError("test %d has %d args, the task has %d params" % (i, len(args), len(ptypes)))
                call = "%s(%s)" % (entry, ", ".join(_rs_lit(env, t, a) for t, a in zip(ptypes, args)))
                out.append('    print!("\\u{1}B%d\\u{2}");' % i)
                out.append("    let r%d = %s;" % (i, call))
                out.append('    print!("\\u{1}E%d\\u{2}{}\\u{3}", r%d.bench_js());' % (i, i))
            out.append("    ::std::io::stdout().flush().unwrap();")
        out.append("}")
        out.append("}")
        out.append("")
        out.append("fn main() {")
        out.append("    bench_harness::run();")
        out.append("}")
        return "\n".join(out) + "\n"

    def _prepare(self, task: Dict[str, Any], code: str, tests: Optional[List[Dict[str, Any]]],
                 workdir: str) -> Tuple[str, int]:
        env = _TypeEnv(task)
        crate = os.path.join(workdir, self.name)
        os.makedirs(os.path.join(crate, "src"), exist_ok=True)
        text = (LANGS_DIR / "Cargo.toml.tmpl").read_text(encoding="utf-8")
        with open(os.path.join(crate, "Cargo.toml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        user = code.replace("\r\n", "\n").rstrip("\n")
        nuser = user.count("\n") + 1 if user else 0
        main = (user + "\n\n" if user else "") + self._harness(task, env, tests)
        with open(os.path.join(crate, "src", "main.rs"), "w", encoding="utf-8", newline="\n") as f:
            f.write(main)
        return crate, nuser

    # -- cargo

    def _cargo(self, crate: str, args: List[str], nuser: int) -> Tuple[bool, List[Dict[str, Any]]]:
        rc, out, err, timed_out = _run(["cargo"] + args, crate, _cargo_env(), self.build_timeout)
        diags = parse_cargo_json(out, nuser)
        if timed_out:
            diags.append(_diag("cargo", "cargo %s timed out after %d s" % (args[0], self.build_timeout), None, err[-2000:]))
        elif rc != 0 and not diags:
            first = next((x for x in err.splitlines() if x.strip()), "cargo %s failed (exit %d)" % (args[0], rc))
            diags.append(_diag("cargo", first.strip(), None, err[-4000:]))
        return (rc == 0 and not timed_out), diags

    def _build(self, crate: str, nuser: int) -> Tuple[bool, List[Dict[str, Any]]]:
        return self._cargo(crate, ["build", "--quiet", "--offline", "--message-format=json"], nuser)

    # -- contract

    def tool_check(self, task: Dict[str, Any], code: str, workdir: str) -> Dict[str, Any]:
        t0 = time.monotonic()
        crate, nuser = self._prepare(task, code, None, workdir)
        ok, diags = self._build(crate, nuser)
        return {"ok": ok, "diagnostics": diags, "tool_ms": _ms(t0)}

    def run_hidden(self, task: Dict[str, Any], code: str, tests: List[Dict[str, Any]],
                   workdir: str) -> Dict[str, Any]:
        t0 = time.monotonic()
        env = _TypeEnv(task)
        rtype = env.parse(task["returns"])
        wants = [canon(env, rtype, t["expect"]) for t in tests]
        crate, nuser = self._prepare(task, code, tests, workdir)
        ok, diags = self._build(crate, nuser)
        if not ok:
            first = diags[0]["message"] if diags else "build failed"
            return _failed(len(tests), "build failed: " + first, wants, t0)
        binary = os.path.join(crate, "target", "debug", "prog")
        rc, out, err, timed_out = _run([binary], crate, _cargo_env(), self.run_timeout)
        if timed_out:
            return _failed(len(tests), "timed out after %g s" % self.run_timeout, wants, t0)
        if rc != 0:
            return _failed(len(tests), "crashed (exit %d): %s" % (rc, crash_summary(err)), wants, t0)
        return _score(tests, wants, out, "", t0)


# ---------------------------------------------------------------- scoring (same logic in ts_strict.py)

def _failed(total: int, reason: str, wants: List[str], t0: float) -> Dict[str, Any]:
    return {"passed": 0, "total": total,
            "failures": [{"index": 0, "got": "<%s>" % reason, "want": wants[0] if wants else ""}],
            "ms": _ms(t0)}


def _render(value: str, stdout: Optional[str]) -> str:
    return value if stdout is None else "%s | stdout=%s" % (value, json.dumps(stdout))


def _score(tests: List[Dict[str, Any]], wants: List[str], out: str, strip_prefix: str, t0: float) -> Dict[str, Any]:
    got_by_index = {}  # type: Dict[int, Tuple[str, str]]
    for m in _MARKER_RE.finditer(out):
        if m.group(1) == m.group(3):
            body = m.group(2)
            if strip_prefix and body.startswith(strip_prefix):
                body = body[len(strip_prefix):]
            got_by_index[int(m.group(1))] = (body, m.group(4))
    passed = 0
    failures = []  # type: List[Dict[str, Any]]
    for i, test in enumerate(tests):
        want_out = test.get("stdout")
        want = _render(wants[i], want_out)
        if i not in got_by_index:
            failures.append({"index": i, "got": "<no result>", "want": want})
            continue
        stdout, raw = got_by_index[i]
        try:
            got_value = json.dumps(json.loads(raw), separators=(",", ":"))
        except ValueError:
            got_value = raw
        got = _render(got_value, stdout if want_out is not None else None)
        if got_value == wants[i] and (want_out is None or stdout == want_out):
            passed += 1
        else:
            failures.append({"index": i, "got": got, "want": want})
    return {"passed": passed, "total": len(tests), "failures": failures, "ms": _ms(t0)}
