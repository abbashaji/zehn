"""zehnlib.analysis: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import json
import os
from zehnlib.errors import DEFAULT_DEPTH, DEFAULT_FUEL, ZehnError, run_guarded
from zehnlib.parser import parse
from zehnlib.fmt import format_program, lock_data
from zehnlib import dialect as dialect_mod
from zehnlib.interp import Interp
from zehnlib.passes import run_static


# ----------------------------------------------------------------------------
# Analysis pipeline + CLI
# ----------------------------------------------------------------------------


def fmt_diag(d):
    loc = d.get("location", {})
    head = "%s %s" % (d["severity"].upper(), d["code"])
    where = ", ".join(str(x) for x in (loc.get("fn"), "line %s" % loc["line"] if "line" in loc else None) if x)
    lines = ["%s [%s]: %s" % (head, where, d["message"])]
    if loc.get("clause"):
        lines.append("    clause : %s" % loc["clause"])
    if d.get("blame"):
        lines.append("    blame  : %s" % d["blame"])
    for k, v in d.get("values", {}).items():
        lines.append("    %-6s : %s" % (k, v))
    for g in d.get("falls_through", []):
        lines.append("    path   : line %d: %s" % (g["line"], g["where"]))
    cs = d.get("call_stack")
    if cs:
        frames = ", ".join(g["fn"] + (" x%d" % g["times"] if g["times"] > 1 else "")
                           for g in cs["innermost"])
        lines.append("    stack  : depth %d, innermost: %s" % (cs["depth"], frames))
    if d.get("via_example"):
        lines.append("    via    : example %s (line %s)" % (d["via_example"]["text"], d["via_example"]["line"]))
    if d.get("fix_hint"):
        lines.append("    hint   : %s" % d["fix_hint"])
    return "\n".join(lines)


def canonical_diags(prog, src, strict):
    canon = format_program(prog)
    if canon == src:
        return []
    a, b = src.split("\n"), canon.split("\n")
    line = next((i + 1 for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)) + 1)
    sev, code = ("error", "E0203") if strict else ("warning", "W0301")
    return [{"code": code, "severity": sev, "phase": "check",
             "message": "source is not in canonical form (first difference at line %d)" % line,
             "location": {"fn": None, "line": line},
             "fix_hint": "run `zehn fmt <file> --write`"}]


def lock_path(path):
    return path + ".lock"


def drift_diags(prog, path):
    """W0201: body/contracts/examples changed while `intent` stayed the same since `zehn lock`."""
    if not path or not os.path.exists(lock_path(path)):
        return []
    try:
        old = json.load(open(lock_path(path), encoding="utf-8")).get("functions", {})
    except (ValueError, OSError):
        return []
    out = []
    for name, cur in lock_data(prog).items():
        was = old.get(name)
        if was and was["impl"] != cur["impl"] and was["intent"] == cur["intent"]:
            out.append({"code": "W0201", "severity": "warning", "phase": "check",
                        "message": "intent drift: the body, contracts or examples of %r changed "
                                   "but its intent did not" % name,
                        "location": {"fn": name, "line": prog.funcs[name].line},
                        "fix_hint": "re-read the intent; if it is still accurate run `zehn lock <file>`"})
    return out




def static_diags(prog, strict=False):
    """Every static pass, in one place, so `check` and `run` can never disagree.
    The passes are a registry (zehnlib.passes): names -> types -> returns, plus any later ones."""
    return run_static(prog, strict)


def nesting_error():
    return ZehnError("E0204", "source is nested too deeply to analyze", "parse",
                     fix_hint="split deeply nested expressions or blocks into helper functions")


def analyze(src, strict=False, path=None, fuel=DEFAULT_FUEL, max_depth=DEFAULT_DEPTH, guard=True,
            dialect=None):
    """parse -> static passes -> canonical/drift -> examples.
    `dialect` ({flag: value}) is in force for the whole call. Returns (prog or None, diagnostics,
    example results)."""
    with dialect_mod.using(dialect or {}):
        return _analyze(src, strict, path, fuel, max_depth, guard)


def _analyze(src, strict, path, fuel, max_depth, guard):
    diags, examples, prog = [], [], None
    try:
        try:
            prog = parse(src)
            diags = static_diags(prog, strict)
            diags += canonical_diags(prog, src, strict)
            diags += drift_diags(prog, path)
        except RecursionError:
            raise nesting_error()
        if not any(d["severity"] == "error" for d in diags):
            def go():
                return Interp(prog, fuel=fuel, max_depth=max_depth).run_examples()
            examples = run_guarded(go, max_depth) if guard else go()
    except ZehnError as z:
        diags = [z.diag]
    return prog, diags, examples
