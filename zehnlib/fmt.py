"""zehnlib.fmt: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import hashlib
import json


# ----------------------------------------------------------------------------
# Canonical formatter + content hashes (SPEC section 10 / invariant 2)
# ----------------------------------------------------------------------------

_BIN_PREC = {"or": 1, "and": 2, "implies": 4, "==": 5, "!=": 5, "<": 5, "<=": 5, ">": 5,
             ">=": 5, "+": 6, "-": 6, "*": 7, "/": 7, "%": 7}
_NON_ASSOC = {"implies", "==", "!=", "<", "<=", ">", ">="}


def fmt_type(t):
    return t.replace(",", ", ")


def fmt_expr(e, need=0):
    """Canonical text of an expression; parenthesised only when precedence demands it."""
    text, prec = _fexpr(e)
    return "(" + text + ")" if prec < need else text


def _fexpr(e):
    k = e.k
    if k == "int":
        return str(e.v), 10
    if k == "str":
        return json.dumps(e.v, ensure_ascii=False), 10
    if k == "bool":
        return ("true" if e.v else "false"), 10
    if k == "name":
        return e.id, 10
    if k == "ctor":
        return e.name, 10
    if k == "list":
        return "[" + ", ".join(fmt_expr(i) for i in e.items) + "]", 10
    if k == "tuple":
        return "(" + ", ".join(fmt_expr(i) for i in e.items) + ")", 10
    if k == "record":
        return "{" + ", ".join("%s: %s" % (n, fmt_expr(v)) for n, v in e.fields) + "}", 10
    if k == "field":
        return fmt_expr(e.obj, 9) + "." + e.name, 9
    if k == "call":
        return fmt_expr(e.fn, 9) + "(" + ", ".join(fmt_expr(a) for a in e.args) + ")", 9
    if k == "try":
        return fmt_expr(e.expr, 9) + "?", 9
    if k == "neg":
        return "-" + fmt_expr(e.expr, 9), 8
    if k == "not":
        return "not " + fmt_expr(e.expr, 4), 3
    if k == "bin":
        p = _BIN_PREC[e.op]
        lmin, rmin = (p + 1, p + 1) if e.op in _NON_ASSOC else (p, p + 1)
        return "%s %s %s" % (fmt_expr(e.l, lmin), e.op, fmt_expr(e.r, rmin)), p
    raise ValueError("cannot format %s" % k)


def fmt_mock_tail(cl):
    """The canonical ` with <effect> = mock [..] ... prints [..]` tail of an example (empty
    unless the dialect `effect_examples=mock` produced one). Mock clauses are sorted by effect."""
    out = ""
    for eff, lst, _line in sorted(getattr(cl, "mocks", None) or (), key=lambda m: m[0]):
        out += " with %s = mock %s" % (eff, fmt_expr(lst))
    prints = getattr(cl, "prints", None)
    if prints is not None:
        out += " prints " + fmt_expr(prints)
    return out


def fmt_pattern(p):
    if p.k == "pwild":
        return "_"
    if p.k == "pbind":
        return p.name
    if p.k == "ptuple":
        return "(" + ", ".join(fmt_pattern(a) for a in p.items) + ")"
    if p.k == "plit":
        if isinstance(p.v, bool):
            return "true" if p.v else "false"
        return json.dumps(p.v, ensure_ascii=False) if isinstance(p.v, str) else str(p.v)
    if p.args:
        return "%s(%s)" % (p.name, ", ".join(fmt_pattern(a) for a in p.args))
    return p.name


class Fmt:
    """Prints a Program in its single canonical form. Full-line comments stay attached to
    the next construct; trailing comments stay on their line."""

    def __init__(self, prog, comments=True):
        self.p = prog
        self.pending = sorted(prog.comments, key=lambda c: c[0]) if comments else []
        self.out = None

    def lead(self, line, ind):
        while self.pending and self.pending[0][0] < line:
            self.out.append("  " * ind + self.pending.pop(0)[1].rstrip())

    def trail(self, line):
        for i, c in enumerate(self.pending):
            if c[0] == line and c[2]:
                self.out[-1] += "  " + c[1].rstrip()
                del self.pending[i]
                return

    def emit(self, line, ind, text):
        self.lead(line, ind)
        self.out.append("  " * ind + text)
        self.trail(line)

    def chunks(self):
        """[(kind, name, text)] in source order; a final ("tail", None, text) holds leftovers."""
        result = []
        for kind, name in self.p.order:
            self.out = []
            if kind == "type":
                self.type_decl(name)
            else:
                self.fn(self.p.funcs[name])
            result.append((kind, name, "\n".join(self.out)))
        if self.pending:
            self.out = []
            self.lead(10 ** 9, 0)
            result.append(("tail", None, "\n".join(self.out)))
        return result

    def type_decl(self, name):
        t = self.p.types[name]
        if t["kind"] == "record":
            body = "{ " + ", ".join("%s: %s" % (n, fmt_type(ty)) for n, ty in t["fields"]) + " }"
        else:
            vs = []
            for vn, _ in t["variants"]:
                args = self.p.variant_args.get(vn, [])
                vs.append(vn + ("(" + ", ".join(fmt_type(a) for a in args) + ")" if args else ""))
            body = " | ".join(vs)
        self.emit(t["line"], 0, "type %s = %s" % (name, body))

    def fn(self, f):
        params = ", ".join("%s: %s" % (n, fmt_type(t)) for n, t in f.params)
        self.emit(f.line, 0, "fn %s(%s) -> %s" % (f.name, params, fmt_type(f.ret)))
        if f.intent is not None:
            self.out.append("  intent " + json.dumps(f.intent, ensure_ascii=False))
        if f.uses:
            self.out.append("  uses [" + ", ".join(sorted(set(f.uses))) + "]")
        for kw, clauses in (("requires", f.requires), ("ensures", f.ensures),
                            ("example", f.examples)):
            for cl in clauses:
                tail = fmt_mock_tail(cl) if kw == "example" else ""
                self.emit(cl.line, 1, "%s %s%s" % (kw, fmt_expr(cl.expr), tail))
        self.out.append("do")
        self.block(f.body, 1)
        self.lead(f.end_line, 1)
        self.out.append("end fn")

    def block(self, stmts, ind):
        for s in stmts:
            self.stmt(s, ind)

    def stmt(self, s, ind):
        k = s.k
        if k in ("let", "var"):
            ann = ": " + fmt_type(s.ann) if s.ann else ""
            self.emit(s.line, ind, "%s %s%s = %s" % (k, s.name, ann, fmt_expr(s.expr)))
        elif k == "assign":
            self.emit(s.line, ind, "%s := %s" % (s.name, fmt_expr(s.expr)))
        elif k == "return":
            self.emit(s.line, ind, "return " + fmt_expr(s.expr))
        elif k == "expr":
            self.emit(s.line, ind, fmt_expr(s.expr))
        elif k == "if":
            self.emit(s.line, ind, "if %s then" % fmt_expr(s.cond))
            self.block(s.then, ind + 1)
            if s.els:
                self.out.append("  " * ind + "else")
                self.block(s.els, ind + 1)
            self.out.append("  " * ind + "end if")
        elif k == "match":
            self.emit(s.line, ind, "match %s do" % fmt_expr(s.subject))
            for p, body, cline in s.cases:
                self.emit(cline, ind + 1, "case %s =>" % fmt_pattern(p))
                self.block(body, ind + 2)
            self.out.append("  " * ind + "end match")


def format_program(prog, comments=True):
    chunks = Fmt(prog, comments).chunks()
    return "\n\n".join(c[2] for c in chunks) + "\n" if chunks else ""


def definition_refs(prog):
    """[{ref, kind, name}] where ref is `fn#a3f9` / `type#c1d2`: the shortest hex prefix
    (at least 4) of the sha256 of the comment-free canonical text that is unique per kind."""
    full = []
    for kind, name, text in Fmt(prog, comments=False).chunks():
        if kind != "tail":
            full.append((kind, name, hashlib.sha256(text.encode("utf-8")).hexdigest()))
    out = []
    for kind, name, h in full:
        n = 4
        while any(k2 == kind and h2 != h and h2[:n] == h[:n] for k2, _, h2 in full):
            n += 1
        out.append({"ref": "%s#%s" % (kind, h[:n]), "kind": kind, "name": name, "hash": h})
    return out


def plain_fn_text(prog, name, with_intent):
    """Comment-free canonical text of one function (optionally without its intent)."""
    f = prog.funcs[name]
    saved = f.intent
    if not with_intent:
        f.intent = None
    try:
        fm = Fmt(prog, comments=False)
        fm.out = []
        fm.fn(f)
        return "\n".join(fm.out)
    finally:
        f.intent = saved


def lock_data(prog):
    """Per-function fingerprints used to detect intent drift (W0201)."""
    data = {}
    for name, f in prog.funcs.items():
        if f.intent is None:
            continue
        data[name] = {
            "intent": hashlib.sha256(f.intent.encode("utf-8")).hexdigest()[:16],
            "impl": hashlib.sha256(plain_fn_text(prog, name, False).encode("utf-8")).hexdigest()[:16],
        }
    return data
