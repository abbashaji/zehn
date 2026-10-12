#!/usr/bin/env python3
"""Zehn v0.3 reference interpreter.

Parses Zehn source, runs static checks (names, arity, mutability, effects,
exhaustiveness), executes programs, and verifies requires / ensures / example.
Every diagnostic is a machine-readable dict (see SPEC.md section 9).

Usage:
    zehn.py check   <file> [--json] [--strict] [--fuel N] [--max-depth N]
    zehn.py run     <file> <fn> '<json-array-of-args>' [--grant console,time.now] [--now N]
                    [--fuel N] [--max-depth N]
    zehn.py fmt     <file> [--write | --check]
    zehn.py hash    <file> [--json]
    zehn.py patch   <file> replace <ref> --with <file|-> [--write]
    zehn.py patch   <file> delete  <ref> [--write]
    zehn.py patch   <file> insert  --with <file|-> [--write]
    zehn.py lock    <file>
    zehn.py explain <code>
"""
import sys
import re
import json
import difflib
import hashlib
import os
import threading
from dataclasses import dataclass

# Deterministic resource limits (SPEC section 13). Both are properties of the *program's*
# semantics, not of the host machine, so a run that exhausts them does so identically everywhere.
DEFAULT_FUEL = 1_000_000      # steps per entry point (one example, or one `run` call)
DEFAULT_DEPTH = 10_000        # nested Zehn calls
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)   # Int is arbitrary precision; fuel (not Python) bounds its size

# ----------------------------------------------------------------------------
# Diagnostics
# ----------------------------------------------------------------------------


class ZehnError(Exception):
    def __init__(self, code, message, phase, **extra):
        super().__init__(message)
        self.diag = {"code": code, "severity": "error", "phase": phase, "message": message}
        self.diag.update(extra)


class Return(Exception):
    def __init__(self, value):
        self.value = value


HINTS = {
    "E0401": "the body or the example is wrong; left is the computed value, right is the expected value",
    "E0501": "check the precondition before calling, or make the function return err",
    "E0502": "fix the implementation or weaken the ensures clause",
    "E0801": "most likely non-terminating recursion: check that every recursive call moves toward a base case",
    "E0802": "most likely unbounded recursion: add or fix the base case; Zehn has no tail-call optimization",
}

EXPLAIN = {
    "E0101": "Lexing error: a character that is not part of the language.",
    "E0201": "Parse error: the token found is not what the grammar allows at this point.",
    "E0202": "Two top-level definitions have the same name.",
    "E0301": "A match does not cover every case. Add the missing cases or a `case _ =>` branch.",
    "E0302": "A name, constructor, or stdlib function does not exist. The fix_hint lists close matches.",
    "E0303": "Wrong number of arguments for a function or constructor.",
    "E0304": "`?` was used in a function whose return type is not Result or Option.",
    "E0305": "Assignment `:=` to a name that was not declared with `var`.",
    "E0203": "Strict mode: the source is not in canonical form. Run `zehn fmt <file> --write`.",
    "E0204": "The source is nested too deeply for the parser (expressions or blocks inside each other). Split it into smaller functions.",
    "E0310": "Some path through the function body reaches the end without `return`. `falls_through` lists every such path. Add a `return` there, or restructure so every `if` has an `else` that returns.",
    "E0306": "Type mismatch found by the static type checker. `expected` and `found` give both types; fix_hint suggests a conversion when one exists.",
    "E0308": "A record literal or field access does not fit any declared record type (unknown field, wrong field set, or not a record).",
    "E0309": "The type cannot be inferred at this point. Add a type annotation, e.g. `let x: Account = ...`.",
    "E0307": "A name is already defined (shadowing is not allowed) or is reserved.",
    "E0401": "An example evaluated to something other than true. Compare left (actual) and right (expected).",
    "E0402": "Strict mode: a function has no example.",
    "E0501": "A precondition (requires) failed. The caller is to blame.",
    "E0502": "A postcondition (ensures) failed. The implementation is to blame.",
    "E0503": "Internal guard: the body ended without `return` at run time. E0310 rejects this statically, so seeing E0503 means the static check was bypassed.",
    "E0504": "Field access on a value that is not a record, or a missing field.",
    "E0505": "Division or modulo by zero. Guard with `requires b != 0`.",
    "E0506": "No case of a match matched at runtime.",
    "E0507": "result.unwrap was applied to an err value.",
    "E0601": "A function calls another function whose effects it did not declare in `uses`.",
    "E0602": "Contracts and examples must be pure: they cannot call functions that have effects.",
    "E0603": "An effectful stdlib function ran inside a function that did not declare the effect in `uses`.",
    "E0604": "The host did not grant a capability the program declared. Pass --grant <effect> to `zehn run`.",
    "E0701": "Patch: no definition has that content hash (it changed, or the ref is wrong). Run `zehn hash` for current refs.",
    "E0702": "Patch: the hash prefix matches several definitions. Use a longer prefix.",
    "E0703": "Patch: the replacement is not exactly one definition of the same kind, or --with is missing.",
    "E0801": "The fuel budget ran out. One step is one expression or statement evaluated, plus a size charge for operations that touch whole lists, texts, maps or big integers. The usual cause is recursion that never reaches its base case; `call_stack` shows where. If the work is genuinely large, raise `--fuel`.",
    "E0802": "The call depth limit was exceeded (default 10000 nested calls). `call_stack` shows the repeating frames. Zehn has no tail-call optimization, so deep recursion over big inputs should use list.fold / list.map instead, or raise `--max-depth`.",
    "W0101": "A function has no example. Add at least one.",
    "W0102": "A statement follows a `return` (or an if/match whose every branch returns), so it can never run. Delete it.",
    "W0201": "Intent drift: body, contracts or examples changed but the intent text did not. Re-read the intent, then run `zehn lock <file>` to confirm.",
    "W0301": "The source is not in canonical form (see `zehn fmt`). An error under --strict (E0203).",
}

# ----------------------------------------------------------------------------
# Values
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class V:
    name: str
    args: tuple = ()


class Rec(dict):
    pass


@dataclass(frozen=True)
class FnRef:
    name: str


class MapV:
    """Immutable insertion-ordered map. Updating an existing key keeps its position."""
    __slots__ = ("items",)

    def __init__(self, items=()):
        self.items = tuple(items)

    def find(self, k):
        for i, (a, _) in enumerate(self.items):
            if eq(a, k):
                return i
        return -1

    def set(self, k, v):
        i = self.find(k)
        if i < 0:
            return MapV(self.items + ((k, v),))
        return MapV(self.items[:i] + ((self.items[i][0], v),) + self.items[i + 1:])

    def remove(self, k):
        i = self.find(k)
        return self if i < 0 else MapV(self.items[:i] + self.items[i + 1:])


UNIT = V("unit")


def eq(a, b):
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, V) and isinstance(b, V):
        return (a.name == b.name and len(a.args) == len(b.args)
                and all(eq(x, y) for x, y in zip(a.args, b.args)))
    if isinstance(a, Rec) and isinstance(b, Rec):
        return a.keys() == b.keys() and all(eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(eq(x, y) for x, y in zip(a, b))
    if isinstance(a, MapV) and isinstance(b, MapV):
        if len(a.items) != len(b.items):
            return False
        for k, v in a.items:
            i = b.find(k)
            if i < 0 or not eq(v, b.items[i][1]):
                return False
        return True
    return a == b


def show(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, V):
        return v.name if not v.args else "%s(%s)" % (v.name, ", ".join(show(a) for a in v.args))
    if isinstance(v, Rec):
        return "{" + ", ".join("%s: %s" % (k, show(x)) for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(show(x) for x in v) + "]"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, FnRef):
        return "<fn %s>" % v.name
    if isinstance(v, MapV):
        return "map{" + ", ".join("%s: %s" % (show(k), show(x)) for k, x in v.items) + "}"
    return str(v)


# ----------------------------------------------------------------------------
# Lexer
# ----------------------------------------------------------------------------

KEYWORDS = {
    "fn", "type", "let", "var", "return", "if", "then", "else", "end", "match", "case",
    "do", "intent", "uses", "requires", "ensures", "example", "implies", "and", "or",
    "not", "true", "false",
}

TOKEN_RE = re.compile(r'''
    (?P<ws>[ \t\r]+)
  | (?P<comment>--[^\n]*)
  | (?P<nl>\n)
  | (?P<int>\d+)
  | (?P<str>"(?:[^"\\\n]|\\.)*")
  | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op>\|>|=>|->|:=|==|!=|<=|>=|[-+*/%<>=(){}\[\],.:|?])
''', re.X)


def tokenize(src, comments=None):
    """Tokens are (kind, value, line, start, end). Comments go to `comments` if given."""
    toks, pos, line = [], 0, 1
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise ZehnError("E0101", "unexpected character %r" % src[pos], "lex",
                            location={"line": line})
        kind, text = m.lastgroup, m.group()
        s, pos = m.start(), m.end()
        if kind in ("ws", "comment"):
            if kind == "comment" and comments is not None:
                trailing = bool(toks) and toks[-1][0] != "NL"
                comments.append((line, text, trailing))
            continue
        if kind == "nl":
            if toks and toks[-1][0] != "NL":
                toks.append(("NL", "\n", line, s, pos))
            line += 1
            continue
        if kind == "int":
            toks.append(("INT", int(text), line, s, pos))
        elif kind == "str":
            toks.append(("STR", json.loads(text), line, s, pos))
        elif kind == "id":
            if text in KEYWORDS:
                toks.append(("KW", text, line, s, pos))
            elif text[0].isupper():
                toks.append(("TID", text, line, s, pos))
            else:
                toks.append(("ID", text, line, s, pos))
        else:
            toks.append(("OP", text, line, s, pos))
    if not toks or toks[-1][0] != "NL":
        toks.append(("NL", "\n", line, len(src), len(src)))
    toks.append(("EOF", None, line, len(src), len(src)))
    return toks


# ----------------------------------------------------------------------------
# AST + parser
# ----------------------------------------------------------------------------


class N:
    def __init__(self, k, line, **kw):
        self.k = k
        self.line = line
        self.__dict__.update(kw)


class Program:
    def __init__(self):
        self.types = {}      # type name -> {"kind": "record"|"sum", ...}
        self.variants = {}   # variant name -> (type name, arity)
        self.funcs = {}      # fn name -> N('fn')
        self.order = []      # [("type"|"fn", name)] in source order
        self.comments = []   # [(line, text, trailing)]
        self.variant_args = {}  # variant name -> [type string]


class Parser:
    def __init__(self, toks, src):
        self.t, self.i, self.src = toks, 0, src

    @property
    def cur(self):
        return self.t[self.i]

    def peek(self, k=1):
        return self.t[min(self.i + k, len(self.t) - 1)]

    def at(self, kind, val=None):
        c = self.cur
        return c[0] == kind and (val is None or c[1] == val)

    def at_kw(self, v):
        return self.at("KW", v)

    def at_op(self, v):
        return self.at("OP", v)

    def err(self, expected):
        c = self.cur
        if c[0] == "NL":
            found = "end of line"
        elif c[0] == "EOF":
            found = "end of file"
        else:
            found = repr(c[1])
        raise ZehnError("E0201", "expected %s, found %s" % (expected, found), "parse",
                        location={"line": c[2]}, expected=expected, found=found)

    def eat(self, kind, val=None):
        if not self.at(kind, val):
            self.err(repr(val) if val else kind)
        tok = self.cur
        self.i += 1
        return tok

    def skip_nl(self):
        while self.at("NL"):
            self.i += 1

    def eol(self):
        if self.at("EOF"):
            return
        self.eat("NL")

    # -- declarations --
    def program(self):
        prog = Program()
        self.skip_nl()
        while not self.at("EOF"):
            if self.at_kw("type"):
                self.type_decl(prog)
            elif self.at_kw("fn"):
                f = self.fn_decl()
                if f.name in prog.funcs:
                    raise ZehnError("E0202", "duplicate function %r" % f.name, "parse",
                                    location={"fn": f.name, "line": f.line})
                prog.funcs[f.name] = f
                prog.order.append(("fn", f.name))
            else:
                self.err("'type' or 'fn'")
            self.skip_nl()
        return prog

    def type_decl(self, prog):
        tline = self.eat("KW", "type")[2]
        name = self.eat("TID")[1]
        if name in prog.types:
            raise ZehnError("E0202", "duplicate type %r" % name, "parse",
                            location={"fn": None, "line": tline})
        prog.order.append(("type", name))
        self.eat("OP", "=")
        if self.at_op("{"):
            self.i += 1
            fields = []
            while True:
                fn_ = self.eat("ID")[1]
                self.eat("OP", ":")
                fields.append((fn_, self.type_()))
                if self.at_op(","):
                    self.i += 1
                else:
                    break
            self.eat("OP", "}")
            prog.types[name] = {"kind": "record", "fields": fields, "line": tline}
        else:
            variants = []
            while True:
                vn = self.eat("TID")[1]
                arity = 0
                vargs = []
                if self.at_op("("):
                    self.i += 1
                    vargs.append(self.type_())
                    arity = 1
                    while self.at_op(","):
                        self.i += 1
                        vargs.append(self.type_())
                        arity += 1
                    self.eat("OP", ")")
                if vn in prog.variants:
                    raise ZehnError("E0202", "duplicate constructor %r" % vn, "parse",
                                    location={"fn": None, "line": tline})
                variants.append((vn, arity))
                prog.variants[vn] = (name, arity)
                prog.variant_args[vn] = vargs
                if self.at_op("|"):
                    self.i += 1
                else:
                    break
            prog.types[name] = {"kind": "sum", "variants": variants, "line": tline}
        self.eol()

    def type_(self):
        if self.at_op("("):
            self.i += 1
            ts = [self.type_()]
            while self.at_op(","):
                self.i += 1
                ts.append(self.type_())
            self.eat("OP", ")")
            return "(" + ",".join(ts) + ")"
        n = self.eat("TID")[1]
        if self.at_op("<"):
            self.i += 1
            ts = [self.type_()]
            while self.at_op(","):
                self.i += 1
                ts.append(self.type_())
            self.eat("OP", ">")
            n += "<" + ",".join(ts) + ">"
        return n

    def clause(self):
        kw = self.cur
        self.i += 1
        first = self.cur
        e = self.expr()
        last = self.t[self.i - 1]
        text = self.src[first[3]:last[4]]
        self.eol()
        return N("clause", kw[2], expr=e, text=text)

    def fn_decl(self):
        line = self.eat("KW", "fn")[2]
        name = self.eat("ID")[1]
        self.eat("OP", "(")
        params = []
        if not self.at_op(")"):
            while True:
                pn = self.eat("ID")[1]
                self.eat("OP", ":")
                params.append((pn, self.type_()))
                if self.at_op(","):
                    self.i += 1
                else:
                    break
        self.eat("OP", ")")
        self.eat("OP", "->")
        ret = self.type_()
        self.eol()
        intent, uses, requires, ensures, examples = None, [], [], [], []
        while True:
            if self.at_kw("intent"):
                self.i += 1
                intent = self.eat("STR")[1]
                self.eol()
            elif self.at_kw("uses"):
                self.i += 1
                self.eat("OP", "[")
                if not self.at_op("]"):
                    while True:
                        eff = self.eat("ID")[1]
                        while self.at_op("."):
                            self.i += 1
                            eff += "." + self.eat("ID")[1]
                        uses.append(eff)
                        if self.at_op(","):
                            self.i += 1
                        else:
                            break
                self.eat("OP", "]")
                self.eol()
            elif self.at_kw("requires"):
                requires.append(self.clause())
            elif self.at_kw("ensures"):
                ensures.append(self.clause())
            elif self.at_kw("example"):
                examples.append(self.clause())
            else:
                break
        self.eat("KW", "do")
        self.eol()
        body = self.block(("end",))
        end_line = self.eat("KW", "end")[2]
        self.eat("KW", "fn")
        self.eol()
        return N("fn", line, name=name, params=params, ret=ret, intent=intent, uses=uses,
                 requires=requires, ensures=ensures, examples=examples, body=body,
                 end_line=end_line)

    # -- statements --
    def block(self, stops):
        out = []
        while True:
            self.skip_nl()
            if self.at("KW") and self.cur[1] in stops:
                return out
            if self.at("EOF"):
                self.err("'end'")
            out.append(self.stmt())

    def stmt(self):
        c = self.cur
        line = c[2]
        if self.at_kw("let") or self.at_kw("var"):
            self.i += 1
            name = self.eat("ID")[1]
            ann = None
            if self.at_op(":"):
                self.i += 1
                ann = self.type_()
            self.eat("OP", "=")
            e = self.expr()
            self.eol()
            return N(c[1], line, name=name, expr=e, ann=ann)
        if self.at_kw("return"):
            self.i += 1
            e = self.expr()
            self.eol()
            return N("return", line, expr=e)
        if self.at_kw("if"):
            self.i += 1
            cond = self.expr()
            self.eat("KW", "then")
            self.eol()
            then = self.block(("else", "end"))
            els = []
            if self.at_kw("else"):
                self.i += 1
                self.eol()
                els = self.block(("end",))
            self.eat("KW", "end")
            self.eat("KW", "if")
            self.eol()
            return N("if", line, cond=cond, then=then, els=els)
        if self.at_kw("match"):
            self.i += 1
            subj = self.expr()
            self.eat("KW", "do")
            self.eol()
            cases = []
            while self.at_kw("case"):
                cline = self.cur[2]
                self.i += 1
                p = self.pattern()
                self.eat("OP", "=>")
                self.eol()
                cases.append((p, self.block(("case", "end")), cline))
            self.eat("KW", "end")
            self.eat("KW", "match")
            self.eol()
            return N("match", line, subject=subj, cases=cases)
        if c[0] == "ID" and self.peek()[0] == "OP" and self.peek()[1] == ":=":
            self.i += 2
            e = self.expr()
            self.eol()
            return N("assign", line, name=c[1], expr=e)
        e = self.expr()
        self.eol()
        return N("expr", line, expr=e)

    def pattern(self):
        c = self.cur
        line = c[2]
        if c[0] == "ID":
            self.i += 1
            if c[1] == "_":
                return N("pwild", line)
            if c[1] in ("ok", "err", "some"):
                self.eat("OP", "(")
                p = self.pattern()
                self.eat("OP", ")")
                return N("pvariant", line, name=c[1], args=[p])
            if c[1] == "none":
                return N("pvariant", line, name="none", args=[])
            return N("pbind", line, name=c[1])
        if c[0] in ("INT", "STR"):
            self.i += 1
            return N("plit", line, v=c[1])
        if self.at_kw("true") or self.at_kw("false"):
            self.i += 1
            return N("plit", line, v=(c[1] == "true"))
        if c[0] == "TID":
            self.i += 1
            args = []
            if self.at_op("("):
                self.i += 1
                args.append(self.pattern())
                while self.at_op(","):
                    self.i += 1
                    args.append(self.pattern())
                self.eat("OP", ")")
            return N("pvariant", line, name=c[1], args=args)
        self.err("a pattern")

    # -- expressions --
    def expr(self):
        left = self.or_()
        while self.at_op("|>"):
            self.i += 1
            right = self.postfix()
            left = self.insert_first(right, left)
        return left

    def insert_first(self, node, left):
        if node.k == "call":
            return N("call", node.line, fn=node.fn, args=[left] + node.args)
        if node.k == "try":
            return N("try", node.line, expr=self.insert_first(node.expr, left))
        return N("call", node.line, fn=node, args=[left])

    def or_(self):
        e = self.and_()
        while self.at_kw("or"):
            line = self.cur[2]
            self.i += 1
            e = N("bin", line, op="or", l=e, r=self.and_())
        return e

    def and_(self):
        e = self.not_()
        while self.at_kw("and"):
            line = self.cur[2]
            self.i += 1
            e = N("bin", line, op="and", l=e, r=self.not_())
        return e

    def not_(self):
        if self.at_kw("not"):
            line = self.cur[2]
            self.i += 1
            return N("not", line, expr=self.implies())
        return self.implies()

    def implies(self):
        e = self.cmp()
        if self.at_kw("implies"):
            line = self.cur[2]
            self.i += 1
            e = N("bin", line, op="implies", l=e, r=self.cmp())
        return e

    def cmp(self):
        e = self.add()
        if self.cur[0] == "OP" and self.cur[1] in ("==", "!=", "<", "<=", ">", ">="):
            line, op = self.cur[2], self.cur[1]
            self.i += 1
            e = N("bin", line, op=op, l=e, r=self.add())
        return e

    def add(self):
        e = self.mul()
        while self.cur[0] == "OP" and self.cur[1] in ("+", "-"):
            line, op = self.cur[2], self.cur[1]
            self.i += 1
            e = N("bin", line, op=op, l=e, r=self.mul())
        return e

    def mul(self):
        e = self.unary()
        while self.cur[0] == "OP" and self.cur[1] in ("*", "/", "%"):
            line, op = self.cur[2], self.cur[1]
            self.i += 1
            e = N("bin", line, op=op, l=e, r=self.unary())
        return e

    def unary(self):
        if self.at_op("-"):
            line = self.cur[2]
            self.i += 1
            return N("neg", line, expr=self.postfix())
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while True:
            line = self.cur[2]
            if self.at_op("."):
                self.i += 1
                e = N("field", line, obj=e, name=self.eat("ID")[1])
            elif self.at_op("("):
                self.i += 1
                args = []
                if not self.at_op(")"):
                    args.append(self.expr())
                    while self.at_op(","):
                        self.i += 1
                        args.append(self.expr())
                self.eat("OP", ")")
                e = N("call", line, fn=e, args=args)
            elif self.at_op("?"):
                self.i += 1
                e = N("try", line, expr=e)
            else:
                return e

    def primary(self):
        c = self.cur
        line = c[2]
        if c[0] == "INT":
            self.i += 1
            return N("int", line, v=c[1])
        if c[0] == "STR":
            self.i += 1
            return N("str", line, v=c[1])
        if self.at_kw("true") or self.at_kw("false"):
            self.i += 1
            return N("bool", line, v=(c[1] == "true"))
        if c[0] == "ID":
            self.i += 1
            return N("name", line, id=c[1])
        if c[0] == "TID":
            self.i += 1
            return N("ctor", line, name=c[1])
        if self.at_op("("):
            self.i += 1
            e = self.expr()
            self.eat("OP", ")")
            return e
        if self.at_op("["):
            self.i += 1
            items = []
            if not self.at_op("]"):
                items.append(self.expr())
                while self.at_op(","):
                    self.i += 1
                    items.append(self.expr())
            self.eat("OP", "]")
            return N("list", line, items=items)
        if self.at_op("{"):
            self.i += 1
            fields = []
            while True:
                fname = self.eat("ID")[1]
                self.eat("OP", ":")
                fields.append((fname, self.expr()))
                if self.at_op(","):
                    self.i += 1
                else:
                    break
            self.eat("OP", "}")
            return N("record", line, fields=fields)
        self.err("an expression")


def parse(src):
    comments = []
    prog = Parser(tokenize(src, comments), src).program()
    prog.comments = comments
    return prog


# ----------------------------------------------------------------------------
# Standard library (tiny, one name per job)
# ----------------------------------------------------------------------------

NONE = V("none")


def _unwrap(it, r):
    if isinstance(r, V) and r.name == "ok":
        return r.args[0]
    raise ZehnError("E0507", "result.unwrap applied to %s" % show(r), "runtime")


def _result_map(it, r, f):
    if isinstance(r, V) and r.name == "ok":
        return V("ok", (it.call_value(f, [r.args[0]]),))
    return r


def _fold(it, xs, init, f):
    acc = init
    for x in xs:
        acc = it.call_value(f, [acc, x])
    return acc


def _option_map(it, o, f):
    if isinstance(o, V) and o.name == "some":
        return V("some", (it.call_value(f, [o.args[0]]),))
    return o


def _result_map_err(it, r, f):
    if isinstance(r, V) and r.name == "err":
        return V("err", (it.call_value(f, [r.args[0]]),))
    return r


def _print(it, t):
    it.stdout.write(t + "\n")
    return UNIT


BUILTIN_EFFECTS = {"console.print": "console", "time.now": "time.now"}

BUILTINS = {
    "list.len": lambda it, xs: len(xs),
    "list.get": lambda it, xs, i: V("some", (xs[i],)) if 0 <= i < len(xs) else NONE,
    "list.append": lambda it, xs, x: xs + [x],
    "list.concat": lambda it, a, b: a + b,
    "list.contains": lambda it, xs, x: any(eq(x, y) for y in xs),
    "list.sum": lambda it, xs: sum(xs),
    "list.map": lambda it, xs, f: [it.call_value(f, [x]) for x in xs],
    "list.filter": lambda it, xs, f: [x for x in xs if it.call_value(f, [x]) is True],
    "list.fold": _fold,
    "text.len": lambda it, t: len(t),
    "text.concat": lambda it, a, b: a + b,
    "text.split_on": lambda it, t, sep: t.split(sep),
    "text.contains": lambda it, t, s: s in t,
    "text.to_upper": lambda it, t: t.upper(),
    "int.to_text": lambda it, n: str(n),
    "int.abs": lambda it, n: abs(n),
    "int.min": lambda it, a, b: min(a, b),
    "int.max": lambda it, a, b: max(a, b),
    "option.unwrap_or": lambda it, o, d: o.args[0] if o.name == "some" else d,
    "option.is_some": lambda it, o: o.name == "some",
    "result.is_ok": lambda it, r: r.name == "ok",
    "result.is_err": lambda it, r: r.name == "err",
    "result.unwrap": _unwrap,
    "result.map": _result_map,
    "result.map_err": _result_map_err,
    "option.map": _option_map,
    "map.empty": lambda it: MapV(),
    "map.set": lambda it, m, k, v: m.set(k, v),
    "map.get": lambda it, m, k: (lambda i: V("some", (m.items[i][1],)) if i >= 0 else NONE)(m.find(k)),
    "map.has": lambda it, m, k: m.find(k) >= 0,
    "map.remove": lambda it, m, k: m.remove(k),
    "map.keys": lambda it, m: [k for k, _ in m.items],
    "map.values": lambda it, m: [v for _, v in m.items],
    "map.len": lambda it, m: len(m.items),
    "console.print": _print,
    "time.now": lambda it: it.clock(),
}
# Builtins whose real work is linear in the size of their arguments; they are charged
# 1 fuel per element / character / 64 bits on top of the 1 step every expression costs.
# (Callbacks of list.map / filter / fold charge themselves as ordinary calls.)
LINEAR_BUILTINS = {
    "list.append", "list.concat", "list.contains", "list.sum", "list.map", "list.filter", "list.fold",
    "text.concat", "text.split_on", "text.contains", "text.to_upper", "int.to_text",
    "map.set", "map.get", "map.has", "map.remove", "map.keys", "map.values",
}


def _size(v):
    if isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return v.bit_length() >> 6
    if isinstance(v, (list, str)):
        return len(v)
    if isinstance(v, MapV):
        return len(v.items)
    return 0


NAMESPACES = {k.split(".")[0] for k in BUILTINS}
CTORS = {"ok", "err", "some", "none"}
RESERVED = NAMESPACES | CTORS | {"out"}


def unparse(n):
    if n.k == "name":
        return n.id
    if n.k == "field":
        o = unparse(n.obj)
        return o + "." + n.name if o else None
    return None


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


def fmt_pattern(p):
    if p.k == "pwild":
        return "_"
    if p.k == "pbind":
        return p.name
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
                self.emit(cl.line, 1, "%s %s" % (kw, fmt_expr(cl.expr)))
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


# ----------------------------------------------------------------------------
# Static checker
# ----------------------------------------------------------------------------


class Checker:
    def __init__(self, prog, strict=False):
        self.p, self.strict, self.diags = prog, strict, []
        self.f = None
        self.in_contract = False
        self.body_calls = []
        self.body_effects = []

    def d(self, code, msg, line, sev="error", **extra):
        diag = {"code": code, "severity": sev, "phase": "check", "message": msg,
                "location": {"fn": self.f.name if self.f else None, "line": line}}
        diag.update(extra)
        self.diags.append(diag)

    def run(self):
        for f in self.p.funcs.values():
            self.check_fn(f)
        return self.diags

    def bind(self, name, kind, sc, line):
        if name in RESERVED:
            self.d("E0307", "name %r is reserved" % name, line)
        elif name in sc or name in self.p.funcs:
            self.d("E0307", "name %r is already defined; shadowing is not allowed" % name, line,
                   fix_hint="choose a different name")
        sc[name] = kind

    def check_fn(self, f):
        self.f, self.body_calls, self.body_effects = f, [], []
        base = {}
        for pn, _ in f.params:
            self.bind(pn, "let", base, f.line)
        self.in_contract = True
        for cl in f.requires:
            self.expr(cl.expr, dict(base))
        for cl in f.ensures:
            self.expr(cl.expr, dict(base, out="let"))
        for cl in f.examples:
            self.expr(cl.expr, {})
        self.in_contract = False
        self.block(f.body, dict(base))
        declared = set(f.uses)
        for callee, line in self.body_calls:
            missing = sorted(set(callee.uses) - declared)
            if missing:
                self.d("E0601", "calls %r which needs effects %s that %r does not declare"
                       % (callee.name, missing, f.name), line,
                       fix_hint="add %s to the `uses [...]` of %s" % (", ".join(missing), f.name))
        for full, eff, line in self.body_effects:
            if eff not in declared:
                self.d("E0601", "calls '%s' which needs effect %r that %r does not declare"
                       % (full, eff, f.name), line,
                       fix_hint="add %s to the `uses [...]` of %s" % (eff, f.name))
        if not f.examples:
            if self.strict:
                self.d("E0402", "function %r has no example (strict mode)" % f.name, f.line,
                       fix_hint="add at least one `example` clause")
            else:
                self.d("W0101", "function %r has no example" % f.name, f.line, sev="warning",
                       fix_hint="add at least one `example` clause")

    def block(self, stmts, sc):
        for s in stmts:
            self.stmt(s, sc)

    def stmt(self, s, sc):
        k = s.k
        if k in ("let", "var"):
            self.expr(s.expr, sc)
            self.bind(s.name, k, sc, s.line)
        elif k == "assign":
            if s.name not in sc:
                self.d("E0302", "unknown name %r" % s.name, s.line)
            elif sc[s.name] != "var":
                self.d("E0305", "cannot assign to %r: it was declared with `let`" % s.name,
                       s.line, fix_hint="declare it with `var`")
            self.expr(s.expr, sc)
        elif k in ("return", "expr"):
            self.expr(s.expr, sc)
        elif k == "if":
            self.expr(s.cond, sc)
            self.block(s.then, dict(sc))
            self.block(s.els, dict(sc))
        elif k == "match":
            self.expr(s.subject, sc)
            for p, body, line in s.cases:
                sc2 = dict(sc)
                self.pbinds(p, sc2)
                self.block(body, sc2)
            self.exhaustive(s)

    def pbinds(self, p, sc):
        if p.k == "pbind":
            self.bind(p.name, "let", sc, p.line)
        elif p.k == "pvariant":
            if p.name in CTORS:
                arity = 0 if p.name == "none" else 1
            elif p.name in self.p.variants:
                arity = self.p.variants[p.name][1]
            else:
                self.d("E0302", "unknown constructor %r in pattern" % p.name, p.line,
                       fix_hint="did you mean: %s" % ", ".join(
                           difflib.get_close_matches(p.name, list(self.p.variants), n=3)))
                arity = len(p.args)
            if arity != len(p.args):
                self.d("E0303", "pattern %s expects %d argument(s), got %d"
                       % (p.name, arity, len(p.args)), p.line)
            for a in p.args:
                self.pbinds(a, sc)

    def exhaustive(self, s):
        pats = [p for p, _, _ in s.cases]
        if any(p.k in ("pwild", "pbind") for p in pats):
            return
        variants = [p for p in pats if p.k == "pvariant"]
        lits = [p for p in pats if p.k == "plit"]
        irrefutable = ("pwild", "pbind")
        covered = {p.name for p in variants if all(a.k in irrefutable for a in p.args)}
        names = {p.name for p in variants}
        if variants and not lits:
            if names <= {"ok", "err"}:
                family = {"ok", "err"}
            elif names <= {"some", "none"}:
                family = {"some", "none"}
            else:
                t = self.p.variants.get(next(iter(names)))
                if not t:
                    return
                family = {vn for vn, _ in self.p.types[t[0]]["variants"]}
            missing = sorted(family - covered)
        elif lits and not variants and all(isinstance(p.v, bool) for p in lits):
            missing = sorted({"true", "false"} - {show(p.v) for p in lits})
        else:
            missing = ["_"]
        if missing:
            self.d("E0301", "non-exhaustive match: missing %s" % ", ".join(missing), s.line,
                   fix_hint="add the missing case(s) or `case _ =>`")

    def record_builtin(self, full, eff, line):
        if self.in_contract:
            self.d("E0602", "contracts and examples must be pure, but %s needs effect %r"
                   % (full, eff), line)
        else:
            self.body_effects.append((full, eff, line))

    def record_call(self, callee, line):
        if self.in_contract:
            if callee.uses:
                self.d("E0602", "contracts and examples must be pure, but %r uses %s"
                       % (callee.name, callee.uses), line)
        else:
            self.body_calls.append((callee, line))

    def expr(self, e, sc):
        k = e.k
        if k in ("int", "str", "bool"):
            return
        if k == "name":
            if e.id in sc or e.id in CTORS:
                return
            if e.id in self.p.funcs:
                self.record_call(self.p.funcs[e.id], e.line)   # fn used as a value
                return
            if e.id in NAMESPACES:
                self.d("E0302", "%r is a stdlib namespace; call a function inside it" % e.id, e.line)
            else:
                near = difflib.get_close_matches(e.id, list(sc) + list(self.p.funcs), n=3)
                self.d("E0302", "unknown name %r" % e.id, e.line,
                       fix_hint="did you mean: %s" % ", ".join(near) if near else "define it first")
        elif k == "ctor":
            if e.name not in self.p.variants:
                near = difflib.get_close_matches(e.name, list(self.p.variants), n=3)
                self.d("E0302", "unknown constructor %r" % e.name, e.line,
                       fix_hint="did you mean: %s" % ", ".join(near) if near else "declare it with `type`")
        elif k == "field":
            o = e.obj
            if o.k == "name" and o.id in NAMESPACES and o.id not in sc:
                full = "%s.%s" % (o.id, e.name)
                if full not in BUILTINS:
                    near = difflib.get_close_matches(
                        full, [b for b in BUILTINS if b.startswith(o.id + ".")], n=3)
                    self.d("E0302", "unknown stdlib function %r" % full, e.line,
                           fix_hint="available: %s" % ", ".join(near) if near else "no such function")
            else:
                self.expr(o, sc)
        elif k == "call":
            fn = e.fn
            if fn.k == "name" and fn.id not in sc and fn.id in self.p.funcs:
                callee = self.p.funcs[fn.id]
                if len(e.args) != len(callee.params):
                    self.d("E0303", "%s expects %d argument(s), got %d"
                           % (fn.id, len(callee.params), len(e.args)), e.line)
                self.record_call(callee, e.line)
            elif fn.k == "name" and fn.id in ("ok", "err", "some") and fn.id not in sc:
                if len(e.args) != 1:
                    self.d("E0303", "%s expects 1 argument" % fn.id, e.line)
            elif fn.k == "ctor":
                self.expr(fn, sc)
                if fn.name in self.p.variants and self.p.variants[fn.name][1] != len(e.args):
                    self.d("E0303", "%s expects %d argument(s), got %d"
                           % (fn.name, self.p.variants[fn.name][1], len(e.args)), e.line)
            else:
                self.expr(fn, sc)
                if (fn.k == "field" and fn.obj.k == "name" and fn.obj.id in NAMESPACES
                        and fn.obj.id not in sc):
                    full = "%s.%s" % (fn.obj.id, fn.name)
                    if full in BUILTIN_EFFECTS:
                        self.record_builtin(full, BUILTIN_EFFECTS[full], e.line)
            for a in e.args:
                self.expr(a, sc)
        elif k == "try":
            if not (self.f.ret.startswith("Result") or self.f.ret.startswith("Option")):
                self.d("E0304", "`?` used in %r whose return type %s is not Result/Option"
                       % (self.f.name, self.f.ret), e.line,
                       fix_hint="change the return type to Result<...> or handle the value with match")
            self.expr(e.expr, sc)
        elif k == "bin":
            self.expr(e.l, sc)
            self.expr(e.r, sc)
        elif k in ("neg", "not"):
            self.expr(e.expr, sc)
        elif k == "list":
            for i in e.items:
                self.expr(i, sc)
        elif k == "record":
            for _, v in e.fields:
                self.expr(v, sc)


# ----------------------------------------------------------------------------
# Return analysis (SPEC section 5): every path of a body must end in `return`
# ----------------------------------------------------------------------------


class ReturnChecker:
    """E0310: some path reaches the end of the body without `return`.
    W0102: a statement follows a point that can never fall through.

    Zehn has no loops, so a structural walk over `if` / `match` is exact: a block always
    returns iff one of its statements is a `return`, or an `if` whose two branches both
    always return, or a `match` whose cases all always return. (`?` returns early, but it
    never *guarantees* a return, so it does not count.) Exhaustiveness of `match` is E0301's
    job; a non-exhaustive match is reported there, not here.
    """

    def __init__(self, prog):
        self.p, self.diags, self.f = prog, [], None

    def run(self):
        for f in self.p.funcs.values():
            self.f = f
            start = {"line": f.body[-1].line if f.body else f.line,
                     "where": "the end of the function body"}
            gaps = self.block(f.body, start)
            if gaps:
                lines = sorted({g["line"] for g in gaps})
                self.diags.append({
                    "code": "E0310", "severity": "error", "phase": "check",
                    "message": "function %r can reach its end without `return` (%d path%s)"
                               % (f.name, len(gaps), "" if len(gaps) == 1 else "s"),
                    "location": {"fn": f.name, "line": lines[0]},
                    "falls_through": gaps,
                    "fix_hint": "add a `return` on every listed path; an `if` without `else` "
                                "never covers its false case"})
        return self.diags

    def warn(self, stmt):
        self.diags.append({
            "code": "W0102", "severity": "warning", "phase": "check",
            "message": "unreachable statement: it follows a `return` or a branch that always returns",
            "location": {"fn": self.f.name, "line": stmt.line},
            "fix_hint": "delete the statement"})

    def block(self, stmts, start):
        """Return the ways control can reach the end of `stmts` (empty list = always returns)."""
        arrivals, live = [start], True
        for i, s in enumerate(stmts):
            if not live:
                self.warn(s)
                break
            if s.k == "return":
                live = False
            elif s.k == "if":
                t = self.block(s.then, {
                    "line": s.then[-1].line if s.then else s.line,
                    "where": "the `then` branch of the `if` at line %d falls off its end" % s.line})
                e = self.block(s.els, {
                    "line": s.els[-1].line if s.els else s.line,
                    "where": ("the `else` branch of the `if` at line %d falls off its end" % s.line)
                             if s.els else
                             "the `if` at line %d has no `else`: when its condition is false "
                             "control continues past it" % s.line})
                if t or e:
                    arrivals = t + e
                else:
                    live = False
            elif s.k == "match":
                falls = []
                for pat, body, line in s.cases:
                    falls += self.block(body, {
                        "line": body[-1].line if body else line,
                        "where": "`case %s` of the `match` at line %d falls off its end"
                                 % (fmt_pattern(pat), s.line)})
                if falls:
                    arrivals = falls
                else:
                    live = False
        return arrivals if live else []


# ----------------------------------------------------------------------------
# Static type checker (SPEC section 3; replaces runtime-only E0306 detection)
# ----------------------------------------------------------------------------


class TVar:
    __slots__ = ("ref",)

    def __init__(self):
        self.ref = None


class TCon:
    __slots__ = ("name", "args")

    def __init__(self, name, args=()):
        self.name, self.args = name, tuple(args)


class TFn:
    __slots__ = ("params", "ret")

    def __init__(self, params, ret):
        self.params, self.ret = tuple(params), ret


INT, BOOL, TEXT, T_UNIT = TCon("Int"), TCon("Bool"), TCon("Text"), TCon("Unit")
PRIMS = {"Int", "Bool", "Text", "Unit"}
GENERIC_ARITY = {"List": 1, "Option": 1, "Result": 2, "Map": 2}


def prune(t):
    while isinstance(t, TVar) and t.ref is not None:
        t = t.ref
    return t


def show_t(t):
    t = prune(t)
    if isinstance(t, TVar):
        return "_"
    if isinstance(t, TFn):
        return "Fn(%s) -> %s" % (", ".join(show_t(p) for p in t.params), show_t(t.ret))
    if t.args:
        return "%s<%s>" % (t.name, ", ".join(show_t(a) for a in t.args))
    return t.name


def _occurs(v, t):
    t = prune(t)
    if t is v:
        return True
    if isinstance(t, TCon):
        return any(_occurs(v, a) for a in t.args)
    if isinstance(t, TFn):
        return any(_occurs(v, p) for p in t.params) or _occurs(v, t.ret)
    return False


def unify(a, b, trail=None):
    a, b = prune(a), prune(b)
    if a is b:
        return True
    if isinstance(a, TVar):
        if _occurs(a, b):
            return False
        a.ref = b
        if trail is not None:
            trail.append(a)
        return True
    if isinstance(b, TVar):
        return unify(b, a, trail)
    if isinstance(a, TCon) and isinstance(b, TCon):
        return (a.name == b.name and len(a.args) == len(b.args)
                and all(unify(x, y, trail) for x, y in zip(a.args, b.args)))
    if isinstance(a, TFn) and isinstance(b, TFn):
        return (len(a.params) == len(b.params)
                and all(unify(x, y, trail) for x, y in zip(a.params, b.params))
                and unify(a.ret, b.ret, trail))
    return False


def try_unify(a, b):
    """Like unify, but a failed attempt leaves no partial bindings behind."""
    trail = []
    ok = unify(a, b, trail)
    if not ok:
        for v in trail:
            v.ref = None
    return ok


_TY_TOK = re.compile(r"\s*(->|[A-Za-z_][A-Za-z0-9_]*|[<>(),])")


def parse_type_text(s, known, svars=None):
    """Type string -> type. `known` = user type names. `svars` (stdlib signatures only) maps
    single capital letters to type variables and enables `Fn(A) -> B`."""
    toks = _TY_TOK.findall(s)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take(x=None):
        t = peek()
        if t is None or (x is not None and t != x):
            raise ValueError("malformed type %r" % s)
        pos[0] += 1
        return t

    def many(close):
        ts = [one()]
        while peek() == ",":
            take(",")
            ts.append(one())
        take(close)
        return ts

    def one():
        t = take()
        if t == "(":
            return TCon("Tuple", many(")"))
        if svars is not None and t == "Fn":
            take("(")
            ps = [] if peek() == ")" else None
            if ps is None:
                ps = many(")")
            else:
                take(")")
            take("->")
            return TFn(ps, one())
        if svars is not None and len(t) == 1 and t.isupper():
            return svars.setdefault(t, TVar())
        if t in GENERIC_ARITY:
            take("<")
            args = many(">")
            if len(args) != GENERIC_ARITY[t]:
                raise ValueError("%s expects %d type argument(s)" % (t, GENERIC_ARITY[t]))
            return TCon(t, args)
        if t in PRIMS or t in known:
            return TCon(t)
        raise ValueError("unknown type %r" % t)

    r = one()
    if pos[0] != len(toks):
        raise ValueError("malformed type %r" % s)
    return r


SIGS = {
    "list.len": "(List<A>) -> Int",
    "list.get": "(List<A>, Int) -> Option<A>",
    "list.append": "(List<A>, A) -> List<A>",
    "list.concat": "(List<A>, List<A>) -> List<A>",
    "list.contains": "(List<A>, A) -> Bool",
    "list.sum": "(List<Int>) -> Int",
    "list.map": "(List<A>, Fn(A) -> B) -> List<B>",
    "list.filter": "(List<A>, Fn(A) -> Bool) -> List<A>",
    "list.fold": "(List<A>, B, Fn(B, A) -> B) -> B",
    "text.len": "(Text) -> Int",
    "text.concat": "(Text, Text) -> Text",
    "text.split_on": "(Text, Text) -> List<Text>",
    "text.contains": "(Text, Text) -> Bool",
    "text.to_upper": "(Text) -> Text",
    "int.to_text": "(Int) -> Text",
    "int.abs": "(Int) -> Int",
    "int.min": "(Int, Int) -> Int",
    "int.max": "(Int, Int) -> Int",
    "option.unwrap_or": "(Option<A>, A) -> A",
    "option.is_some": "(Option<A>) -> Bool",
    "option.map": "(Option<A>, Fn(A) -> B) -> Option<B>",
    "result.is_ok": "(Result<A, E>) -> Bool",
    "result.is_err": "(Result<A, E>) -> Bool",
    "result.unwrap": "(Result<A, E>) -> A",
    "result.map": "(Result<A, E>, Fn(A) -> B) -> Result<B, E>",
    "result.map_err": "(Result<A, E>, Fn(E) -> F) -> Result<A, F>",
    "map.empty": "() -> Map<K, V>",
    "map.set": "(Map<K, V>, K, V) -> Map<K, V>",
    "map.get": "(Map<K, V>, K) -> Option<V>",
    "map.has": "(Map<K, V>, K) -> Bool",
    "map.remove": "(Map<K, V>, K) -> Map<K, V>",
    "map.keys": "(Map<K, V>) -> List<K>",
    "map.values": "(Map<K, V>) -> List<V>",
    "map.len": "(Map<K, V>) -> Int",
    "console.print": "(Text) -> Unit",
    "time.now": "() -> Int",
}


def instantiate(sig):
    """Fresh (param types, return type) for a stdlib signature string."""
    svars = {}
    # find the `)` that closes the parameter list
    depth, cut = 0, None
    for i, ch in enumerate(sig):
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0:
            cut = i
            break
    params_s, ret_s = sig[1:cut], sig[cut + 1:].split("->", 1)[1]
    params = []
    if params_s.strip():
        depth, cur, prev = 0, "", ""
        for ch in params_s:
            if ch in "(<":
                depth += 1
            elif ch in ")>" and not (ch == ">" and prev == "-"):
                depth -= 1
            prev = ch
            if ch == "," and depth == 0:
                params.append(cur)
                cur = ""
            else:
                cur += ch
        params.append(cur)
    return ([parse_type_text(p.strip(), (), svars) for p in params],
            parse_type_text(ret_s.strip(), (), svars))


class TypeChecker:
    """Bidirectional inference with unification. Functions already rejected by the name
    checker are skipped (`skip`) so one mistake does not cascade."""

    def __init__(self, prog, skip=()):
        self.p, self.skip, self.diags = prog, set(skip), []
        self.f = None
        self.ret = None
        self.rec_fields = {}   # record type name -> {field: type}
        self.vtypes = {}       # variant name -> [arg types]
        self.sigs = {}

    # -- plumbing --
    def d(self, code, msg, line, **extra):
        diag = {"code": code, "severity": "error", "phase": "check", "message": msg,
                "location": {"fn": self.f.name if self.f else None, "line": line}}
        diag.update(extra)
        self.diags.append(diag)

    def ty(self, text, line):
        try:
            return parse_type_text(text, self.p.types)
        except ValueError as ex:
            near = difflib.get_close_matches(text.split("<")[0], list(self.p.types) + sorted(PRIMS)
                                             + sorted(GENERIC_ARITY), n=3)
            self.d("E0302", str(ex), line,
                   fix_hint=("did you mean: %s" % ", ".join(near)) if near else "declare it with `type`")
            return TVar()

    def mismatch(self, line, want, got, ctx=None):
        w, g = show_t(want), show_t(got)
        hint = None
        gp, wp = prune(got), prune(want)
        if w == "Text" and g == "Int":
            hint = "convert with int.to_text(...)"
        elif isinstance(gp, TCon) and gp.name == "Option" and unify_probe(gp.args[0], wp):
            hint = "unwrap with option.unwrap_or(default) or a match"
        elif isinstance(gp, TCon) and gp.name == "Result" and unify_probe(gp.args[0], wp):
            hint = "propagate with `?` (in a Result-returning fn) or use a match"
        self.d("E0306", "type mismatch%s: expected %s, found %s"
               % (" in " + ctx if ctx else "", w, g), line, expected=w, found=g,
               **({"fix_hint": hint} if hint else {}))

    def expect(self, e, want, sc, ctx=None):
        got = self.infer(e, sc, want)
        if not unify(got, want):
            self.mismatch(e.line, want, got, ctx)

    def fn_sig(self, f):
        if f.name not in self.sigs:
            self.sigs[f.name] = TFn([self.ty(t, f.line) for _, t in f.params], self.ty(f.ret, f.line))
        return self.sigs[f.name]

    # -- driver --
    def run(self):
        for name, t in self.p.types.items():
            self.f = None
            if t["kind"] == "record":
                self.rec_fields[name] = {}
        for name, t in self.p.types.items():
            if t["kind"] == "record":
                for fname, ftxt in t["fields"]:
                    self.rec_fields[name][fname] = self.ty(ftxt, t["line"])
            else:
                for vn, _ in t["variants"]:
                    self.vtypes[vn] = [self.ty(a, t["line"]) for a in self.p.variant_args.get(vn, [])]
        for f in self.p.funcs.values():
            if f.name not in self.skip:
                self.check_fn(f)
        return self.diags

    def check_fn(self, f):
        self.f = f
        sig = self.fn_sig(f)
        self.ret = sig.ret
        sc = {pn: pt for (pn, _), pt in zip(f.params, sig.params)}
        for cl in f.requires:
            self.expect(cl.expr, BOOL, dict(sc), "requires")
        for cl in f.ensures:
            self.expect(cl.expr, BOOL, dict(sc, out=self.ret), "ensures")
        for cl in f.examples:
            self.expect(cl.expr, BOOL, {}, "example")
        self.block(f.body, dict(sc))

    # -- statements --
    def block(self, stmts, sc):
        for s in stmts:
            self.stmt(s, sc)

    def stmt(self, s, sc):
        k = s.k
        if k in ("let", "var"):
            if s.ann:
                want = self.ty(s.ann, s.line)
                self.expect(s.expr, want, sc, "%s %s" % (k, s.name))
                sc[s.name] = want
            else:
                sc[s.name] = self.infer(s.expr, sc)
        elif k == "assign":
            want = sc.get(s.name)
            if want is None:
                self.infer(s.expr, sc)
            else:
                self.expect(s.expr, want, sc, "assignment to %s" % s.name)
        elif k == "return":
            self.expect(s.expr, self.ret, sc, "return")
        elif k == "expr":
            self.infer(s.expr, sc)
        elif k == "if":
            self.expect(s.cond, BOOL, sc, "if condition")
            self.block(s.then, dict(sc))
            self.block(s.els, dict(sc))
        elif k == "match":
            subj = self.infer(s.subject, sc)
            for p, body, _ in s.cases:
                sc2 = dict(sc)
                self.pattern(p, subj, sc2)
                self.block(body, sc2)

    def pattern(self, p, t, sc):
        k = p.k
        if k == "pwild":
            return
        if k == "pbind":
            sc[p.name] = t
            return
        if k == "plit":
            lt = BOOL if isinstance(p.v, bool) else TEXT if isinstance(p.v, str) else INT
            if not unify(t, lt):
                self.d("E0306", "pattern of type %s does not match %s" % (show_t(lt), show_t(t)),
                       p.line, expected=show_t(t), found=show_t(lt))
            return
        name = p.name
        if name in ("ok", "err"):
            a, b = TVar(), TVar()
            whole, inner = TCon("Result", [a, b]), (a if name == "ok" else b)
            subs = [inner]
        elif name in ("some", "none"):
            a = TVar()
            whole, subs = TCon("Option", [a]), ([a] if name == "some" else [])
        elif name in self.vtypes:
            whole, subs = TCon(self.p.variants[name][0]), self.vtypes[name]
        else:
            return
        if not unify(t, whole):
            self.d("E0306", "pattern %s does not match %s" % (name, show_t(t)), p.line,
                   expected=show_t(t), found=show_t(whole))
            return
        for sp, st in zip(p.args, subs):
            self.pattern(sp, st, sc)

    # -- expressions --
    def infer(self, e, sc, exp=None):
        k = e.k
        if k == "int":
            return INT
        if k == "str":
            return TEXT
        if k == "bool":
            return BOOL
        if k == "name":
            if e.id in sc:
                return sc[e.id]
            if e.id == "none":
                t = TCon("Option", [TVar()])
                if exp is not None:
                    try_unify(t, exp)
                return t
            if e.id in self.p.funcs:
                return self.fn_sig(self.p.funcs[e.id])
            return TVar()
        if k == "ctor":
            if e.name in self.vtypes:
                if self.vtypes[e.name]:
                    self.d("E0303", "%s needs %d argument(s)" % (e.name, len(self.vtypes[e.name])), e.line)
                return TCon(self.p.variants[e.name][0])
            return TVar()
        if k == "list":
            return self.list_(e, sc, exp)
        if k == "record":
            return self.record(e, sc, exp)
        if k == "field":
            return self.field(e, sc)
        if k == "call":
            return self.call(e, sc, exp)
        if k == "try":
            return self.try_(e, sc)
        if k == "neg":
            self.expect(e.expr, INT, sc, "negation")
            return INT
        if k == "not":
            self.expect(e.expr, BOOL, sc, "not")
            return BOOL
        if k == "bin":
            return self.bin(e, sc)
        return TVar()

    def list_(self, e, sc, exp):
        elem = TVar()
        px = prune(exp) if exp is not None else None
        if isinstance(px, TCon) and px.name == "List":
            try_unify(elem, px.args[0])
        for item in e.items:
            t = self.infer(item, sc, elem)
            if not unify(elem, t):
                self.mismatch(item.line, elem, t, "list element")
        return TCon("List", [elem])

    def record(self, e, sc, exp):
        names = [n for n, _ in e.fields]
        if len(set(names)) != len(names):
            self.d("E0308", "duplicate field in record literal", e.line)
        px = prune(exp) if exp is not None else None
        target = None
        if isinstance(px, TCon) and px.name in self.rec_fields:
            target = px.name
        else:
            cands = [n for n, fs in self.rec_fields.items() if set(fs) == set(names)]
            if len(cands) == 1:
                target = cands[0]
            elif len(cands) > 1:
                self.d("E0309", "record {%s} could be %s; the type cannot be inferred here"
                       % (", ".join(names), " or ".join(cands)), e.line,
                       fix_hint="bind it with a type annotation: `let x: %s = ...`" % cands[0])
            else:
                self.d("E0308", "no record type has exactly the fields {%s}" % ", ".join(names), e.line,
                       fix_hint="declare it with `type Name = { ... }`")
        if target is None:
            for _, v in e.fields:
                self.infer(v, sc)
            return TVar()
        fs = self.rec_fields[target]
        if set(fs) != set(names):
            self.d("E0308", "record %s has fields {%s} but the literal has {%s}"
                   % (target, ", ".join(fs), ", ".join(names)), e.line)
            for _, v in e.fields:
                self.infer(v, sc)
        else:
            for n, v in e.fields:
                self.expect(v, fs[n], sc, "field %s of %s" % (n, target))
        return TCon(target)

    def field(self, e, sc):
        o = e.obj
        if o.k == "name" and o.id in NAMESPACES and o.id not in sc:
            self.d("E0306", "stdlib function %s.%s cannot be used as a value; wrap it in a named fn"
                   % (o.id, e.name), e.line)
            return TVar()
        t = prune(self.infer(o, sc))
        if isinstance(t, TCon) and t.name in self.rec_fields:
            fs = self.rec_fields[t.name]
            if e.name in fs:
                return fs[e.name]
            near = difflib.get_close_matches(e.name, list(fs), n=3)
            self.d("E0308", "type %s has no field %r" % (t.name, e.name), e.line,
                   fix_hint="fields: %s" % ", ".join(near or fs))
            return TVar()
        if isinstance(t, TVar):
            self.d("E0309", "cannot infer the type of the value before `.%s`" % e.name, e.line,
                   fix_hint="add a type annotation to the `let`")
        else:
            self.d("E0308", "field access .%s on non-record type %s" % (e.name, show_t(t)), e.line)
        return TVar()

    def call(self, e, sc, exp):
        fn, args = e.fn, e.args
        if fn.k == "field" and fn.obj.k == "name" and fn.obj.id in NAMESPACES and fn.obj.id not in sc:
            full = "%s.%s" % (fn.obj.id, fn.name)
            if full not in SIGS:
                for a in args:
                    self.infer(a, sc)
                return TVar()
            params, ret = instantiate(SIGS[full])
            self.args(full, params, args, sc, e.line)
            if exp is not None:
                try_unify(ret, exp)     # only fills still-unknown type variables, e.g. map.empty()
            return ret
        if fn.k == "name" and fn.id in ("ok", "err", "some") and fn.id not in sc:
            a, b = TVar(), TVar()
            if fn.id == "some":
                t, slot = TCon("Option", [a]), a
            else:
                t, slot = TCon("Result", [a, b]), (a if fn.id == "ok" else b)
            if exp is not None:
                try_unify(t, exp)
            self.args(fn.id, [slot], args, sc, e.line)
            return t
        if fn.k == "ctor" and fn.name in self.vtypes:
            self.args(fn.name, self.vtypes[fn.name], args, sc, e.line)
            return TCon(self.p.variants[fn.name][0])
        if fn.k == "name" and fn.id not in sc and fn.id in self.p.funcs:
            sig = self.fn_sig(self.p.funcs[fn.id])
            self.args(fn.id, list(sig.params), args, sc, e.line)
            return sig.ret
        ct = prune(self.infer(fn, sc))
        if isinstance(ct, TFn):
            self.args("function value", list(ct.params), args, sc, e.line)
            return ct.ret
        for a in args:
            self.infer(a, sc)
        if not isinstance(ct, TVar):
            self.d("E0306", "value of type %s is not callable" % show_t(ct), e.line)
        return TVar()

    def args(self, who, params, args, sc, line):
        if len(params) != len(args):
            self.d("E0303", "%s expects %d argument(s), got %d" % (who, len(params), len(args)), line)
        for i, a in enumerate(args):
            if i < len(params):
                self.expect(a, params[i], sc, "argument %d of %s" % (i + 1, who))
            else:
                self.infer(a, sc)

    def try_(self, e, sc):
        t = prune(self.infer(e.expr, sc))
        r = prune(self.ret)
        if isinstance(t, TCon) and t.name in ("Result", "Option"):
            if not (isinstance(r, TCon) and r.name == t.name):
                self.d("E0306", "`?` on %s inside %r, which returns %s"
                       % (show_t(t), self.f.name, show_t(r)), e.line,
                       fix_hint="make the function return %s<...> or use a match" % t.name)
            elif t.name == "Result" and not unify(t.args[1], r.args[1]):
                self.d("E0306", "`?` propagates error type %s but %r returns error type %s"
                       % (show_t(t.args[1]), self.f.name, show_t(r.args[1])), e.line,
                       expected=show_t(r.args[1]), found=show_t(t.args[1]),
                       fix_hint="the error types must match exactly; convert with result.map_err")
            return t.args[0]
        if isinstance(t, TVar):
            self.d("E0309", "cannot infer the type before `?`", e.line)
        else:
            self.d("E0306", "`?` needs a Result or Option, found %s" % show_t(t), e.line)
        return TVar()

    def bin(self, e, sc):
        op = e.op
        if op in ("and", "or", "implies"):
            self.expect(e.l, BOOL, sc, "`%s`" % op)
            self.expect(e.r, BOOL, sc, "`%s`" % op)
            return BOOL
        if op in ("==", "!="):
            lt = self.infer(e.l, sc)
            rt = self.infer(e.r, sc, lt)
            if not unify(lt, rt):
                self.mismatch(e.r.line, lt, rt, "comparison")
            return BOOL
        self.expect(e.l, INT, sc, "`%s`" % op)
        self.expect(e.r, INT, sc, "`%s`" % op)
        return INT if op in ("+", "-", "*", "/", "%") else BOOL


def unify_probe(a, b):
    """Would a and b unify? (does not keep bindings for concrete types)"""
    a, b = prune(a), prune(b)
    if isinstance(a, TVar) or isinstance(b, TVar):
        return False
    return show_t(a) == show_t(b)


# ----------------------------------------------------------------------------
# Interpreter
# ----------------------------------------------------------------------------


class Interp:
    def __init__(self, prog, granted=(), now=None, stdout=None,
                 fuel=DEFAULT_FUEL, max_depth=DEFAULT_DEPTH):
        self.p = prog
        self.granted = set(granted)   # capabilities the HOST grants (never more than declared)
        self.frames = []              # stack of effect sets declared by running functions
        self.stack = []               # names of running functions, outermost first
        self.now = now
        self.stdout = stdout or sys.stdout
        self.fuel_limit, self.max_depth = fuel, max_depth
        self.used = 0                 # fuel spent in the current entry point
        self.line = None              # line of the call being made (for diagnostics)

    # -- deterministic resource limits (SPEC section 13) --
    def fresh_budget(self):
        """Start a new entry point (one example, or one `run`): full fuel, empty stack."""
        self.used = 0
        self.stack, self.frames = [], []

    def invoke(self, f, args):
        """The public entry point for running one function: fresh budget, a stack big enough
        for `max_depth`, and no raw Python RecursionError can escape (it becomes E0802)."""
        def go():
            self.fresh_budget()
            try:
                return self.call_fn(f, args)
            except RecursionError:
                raise host_stack_error()
        return run_guarded(go, self.max_depth)

    def stack_summary(self):
        """Innermost frames, run-length encoded, plus the most frequent function."""
        tail, groups = self.stack[-12:], []
        for name in tail:
            if groups and groups[-1]["fn"] == name:
                groups[-1]["times"] += 1
            else:
                groups.append({"fn": name, "times": 1})
        counts = {}
        for name in self.stack:
            counts[name] = counts.get(name, 0) + 1
        top = max(counts.items(), key=lambda kv: kv[1]) if counts else (None, 0)
        return {"depth": len(self.stack), "innermost": groups, "most_frequent": top[0],
                "most_frequent_count": top[1]}

    def limit_error(self, code, msg, line, **limits):
        sm = self.stack_summary()
        hint = HINTS[code]
        if sm["most_frequent"] and sm["most_frequent_count"] >= 20:
            hint = "function %r is on the call stack %d times: check its base case; %s" % (
                sm["most_frequent"], sm["most_frequent_count"], hint)
        return ZehnError(code, msg, "runtime", blame="callee",
                         location={"fn": self.stack[-1] if self.stack else None, "line": line},
                         call_stack=sm, fix_hint=hint, **limits)

    def tick(self, line, n=1):
        self.used += n
        if self.used > self.fuel_limit:
            raise self.limit_error("E0801", "fuel exhausted after %d steps" % self.fuel_limit, line,
                                   fuel_limit=self.fuel_limit)

    def clock(self):
        import time as _time
        return self.now if self.now is not None else int(_time.time())

    def need(self, eff, full, line):
        frame = self.frames[-1] if self.frames else set()
        if eff not in frame:
            raise ZehnError("E0603", "%s needs effect %r but the running function does not declare it"
                            % (full, eff), "runtime", blame="callee", location={"line": line},
                            fix_hint="add %s to the `uses [...]` of the calling function" % eff)
        if eff not in self.granted:
            raise ZehnError("E0604", "capability %r is not granted by the host" % eff, "runtime",
                            blame="host", location={"line": line},
                            fix_hint="re-run with --grant %s" % eff)

    # -- helpers --
    def bool_(self, x, e):
        if not isinstance(x, bool):
            raise ZehnError("E0306", "expected Bool, got %s" % show(x), "runtime",
                            location={"line": e.line})
        return x

    def int_(self, x, e):
        if isinstance(x, bool) or not isinstance(x, int):
            raise ZehnError("E0306", "expected Int, got %s" % show(x), "runtime",
                            location={"line": e.line})
        return x

    def call_value(self, f, args):
        if isinstance(f, FnRef):
            return self.call_fn(self.p.funcs[f.name], args)
        raise ZehnError("E0306", "%s is not callable" % show(f), "runtime")

    # -- functions with contracts --
    def call_fn(self, f, args):
        if len(self.stack) >= self.max_depth:
            raise self.limit_error("E0802", "call depth limit of %d exceeded" % self.max_depth,
                                   self.line, depth_limit=self.max_depth)
        self.frames.append(set(f.uses))
        self.stack.append(f.name)
        try:
            return self._call_fn(f, args)
        finally:
            self.stack.pop()
            self.frames.pop()

    def _call_fn(self, f, args):
        if len(args) != len(f.params):
            raise ZehnError("E0303", "%s expects %d argument(s), got %d"
                            % (f.name, len(f.params), len(args)), "runtime")
        env = {pn: a for (pn, _), a in zip(f.params, args)}
        for cl in f.requires:
            if self.eval(cl.expr, env) is not True:
                raise self.contract_error("E0501", "precondition failed", "caller", f, cl, env)
        try:
            self.exec_block(f.body, env)
        except Return as r:
            out = r.value
        else:
            raise ZehnError("E0503", "function %r ended without return" % f.name, "runtime",
                            location={"fn": f.name, "line": f.line})
        env2 = dict(env, out=out)
        for cl in f.ensures:
            if self.eval(cl.expr, env2) is not True:
                raise self.contract_error("E0502", "postcondition failed", "callee", f, cl, env2)
        return out

    def contract_error(self, code, msg, blame, f, cl, env):
        return ZehnError(code, msg, "runtime", blame=blame,
                         location={"fn": f.name, "line": cl.line, "clause": cl.text},
                         values=self.explain(cl.expr, env), fix_hint=HINTS[code])

    def explain(self, expr, env):
        seen = {}

        def walk(n):
            if isinstance(n, N):
                if n.k in ("name", "field"):
                    key = unparse(n)
                    if key and key not in seen:
                        try:
                            val = show(self.eval(n, env))
                            if not val.startswith("<fn ") and val != key:
                                seen[key] = val
                        except Exception:
                            pass
                    if n.k == "field":
                        walk(n.obj)
                    return
                for v in n.__dict__.values():
                    walk(v)
            elif isinstance(n, (list, tuple)):
                for x in n:
                    walk(x)

        walk(expr)
        if expr.k == "bin" and expr.op in ("==", "!=", "<", "<=", ">", ">="):
            try:
                seen["left"] = show(self.eval(expr.l, env))
                seen["right"] = show(self.eval(expr.r, env))
            except ZehnError:
                pass
        return seen

    # -- statements --
    def exec_block(self, stmts, env):
        for s in stmts:
            self.exec(s, env)

    def exec(self, s, env):
        k = s.k
        self.used += 1
        if self.used > self.fuel_limit:
            self.tick(s.line, 0)
        if k in ("let", "var", "assign"):
            env[s.name] = self.eval(s.expr, env)
        elif k == "return":
            raise Return(self.eval(s.expr, env))
        elif k == "if":
            branch = s.then if self.bool_(self.eval(s.cond, env), s.cond) else s.els
            self.exec_block(branch, env)
        elif k == "match":
            v = self.eval(s.subject, env)
            for p, body, _ in s.cases:
                b = self.pmatch(p, v)
                if b is not None:
                    env.update(b)
                    self.exec_block(body, env)
                    return
            raise ZehnError("E0506", "no case matched %s" % show(v), "runtime",
                            location={"line": s.line})
        else:
            self.eval(s.expr, env)

    def pmatch(self, p, v):
        k = p.k
        if k == "pwild":
            return {}
        if k == "pbind":
            return {p.name: v}
        if k == "plit":
            return {} if eq(p.v, v) else None
        if isinstance(v, V) and v.name == p.name and len(v.args) == len(p.args):
            out = {}
            for sp, sv in zip(p.args, v.args):
                b = self.pmatch(sp, sv)
                if b is None:
                    return None
                out.update(b)
            return out
        return None

    # -- expressions --
    def eval(self, e, env):
        k = e.k
        self.used += 1
        if self.used > self.fuel_limit:
            self.tick(e.line, 0)
        if k in ("int", "str", "bool"):
            return e.v
        if k == "name":
            if e.id in env:
                return env[e.id]
            if e.id == "none":
                return NONE
            if e.id in self.p.funcs:
                return FnRef(e.id)
            raise ZehnError("E0302", "unknown name %r" % e.id, "runtime", location={"line": e.line})
        if k == "ctor":
            if self.p.variants[e.name][1] == 0:
                return V(e.name)
            raise ZehnError("E0303", "%s needs arguments" % e.name, "runtime", location={"line": e.line})
        if k == "list":
            return [self.eval(i, env) for i in e.items]
        if k == "record":
            return Rec((n, self.eval(v, env)) for n, v in e.fields)
        if k == "field":
            o = self.eval(e.obj, env)
            if isinstance(o, Rec) and e.name in o:
                return o[e.name]
            raise ZehnError("E0504", "no field %r on %s" % (e.name, show(o)), "runtime",
                            location={"line": e.line})
        if k == "neg":
            return -self.int_(self.eval(e.expr, env), e)
        if k == "not":
            return not self.bool_(self.eval(e.expr, env), e)
        if k == "try":
            v = self.eval(e.expr, env)
            if isinstance(v, V) and v.name in ("ok", "some"):
                return v.args[0]
            if isinstance(v, V) and v.name in ("err", "none"):
                raise Return(v)
            raise ZehnError("E0306", "`?` applied to %s" % show(v), "runtime", location={"line": e.line})
        if k == "bin":
            return self.binop(e, env)
        if k == "call":
            return self.call(e, env)
        raise ZehnError("E0306", "cannot evaluate %s" % k, "runtime")

    def binop(self, e, env):
        op = e.op
        if op == "and":
            return self.bool_(self.eval(e.l, env), e.l) and self.bool_(self.eval(e.r, env), e.r)
        if op == "or":
            return self.bool_(self.eval(e.l, env), e.l) or self.bool_(self.eval(e.r, env), e.r)
        if op == "implies":
            return (not self.bool_(self.eval(e.l, env), e.l)) or self.bool_(self.eval(e.r, env), e.r)
        a, b = self.eval(e.l, env), self.eval(e.r, env)
        if op == "==":
            return eq(a, b)
        if op == "!=":
            return not eq(a, b)
        a, b = self.int_(a, e.l), self.int_(b, e.r)
        # Big integers cost fuel by size, charged BEFORE computing so that a runaway product is
        # stopped instead of allocating gigabytes. Model: 64-bit words wa, wb; `+ -` cost
        # max(wa, wb); `* / %` cost wa*wb (schoolbook). Operands up to 128 bits are free.
        if a.bit_length() > 128 or b.bit_length() > 128:
            wa, wb = (a.bit_length() >> 6) + 1, (b.bit_length() >> 6) + 1
            self.tick(e.line, max(wa, wb) if op in ("+", "-") else wa * wb)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op in ("/", "%"):
            if b == 0:
                raise ZehnError("E0505", "division by zero", "runtime", location={"line": e.line},
                                blame="caller", fix_hint="guard with `requires b != 0`")
            return a // b if op == "/" else a % b
        return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]

    def call(self, e, env):
        fn = e.fn
        if (fn.k == "field" and fn.obj.k == "name" and fn.obj.id in NAMESPACES
                and fn.obj.id not in env):
            full = "%s.%s" % (fn.obj.id, fn.name)
            args = [self.eval(a, env) for a in e.args]
            self.line = e.line
            if full in LINEAR_BUILTINS:
                self.tick(e.line, sum(_size(a) for a in args))
            if full == "int.to_text":
                self.tick(e.line, (_size(args[0]) + 1) ** 2 // 4)
            if full in BUILTIN_EFFECTS:
                self.need(BUILTIN_EFFECTS[full], full, e.line)
            try:
                return BUILTINS[full](self, *args)
            except ZehnError:
                raise
            except Return:
                raise
            except (TypeError, AttributeError, ValueError, IndexError):
                raise ZehnError("E0306", "bad arguments for %s: %s"
                                % (full, ", ".join(show(a) for a in args)), "runtime",
                                location={"line": e.line})
        args = [self.eval(a, env) for a in e.args]
        self.line = e.line
        if fn.k == "name" and fn.id not in env:
            if fn.id in self.p.funcs:
                return self.call_fn(self.p.funcs[fn.id], args)
            if fn.id in ("ok", "err", "some"):
                return V(fn.id, (args[0],))
        if fn.k == "ctor":
            return V(fn.name, tuple(args))
        return self.call_value(self.eval(fn, env), args)

    # -- examples --
    def run_examples(self):
        results = []
        for f in self.p.funcs.values():
            for ex in f.examples:
                rec = {"fn": f.name, "line": ex.line, "example": ex.text}
                self.fresh_budget()
                try:
                    ok = self.eval(ex.expr, {})
                    if ok is True:
                        rec["status"] = "pass"
                    else:
                        rec["status"] = "fail"
                        rec["diag"] = {
                            "code": "E0401", "severity": "error", "phase": "runtime",
                            "message": "example is not true",
                            "location": {"fn": f.name, "line": ex.line, "clause": "example " + ex.text},
                            "values": self.explain(ex.expr, {}), "fix_hint": HINTS["E0401"]}
                except (ZehnError, RecursionError) as z:
                    if isinstance(z, RecursionError):
                        z = host_stack_error()
                    rec["status"] = "fail"
                    z.diag.setdefault("location", {})
                    z.diag["via_example"] = {"fn": f.name, "line": ex.line, "text": ex.text}
                    rec["diag"] = z.diag
                results.append(rec)
        return results


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


def host_stack_error():
    """Backstop: the host's own stack ran out before the semantic depth limit did (this needs
    pathologically nested *expressions*, not deep recursion). Same code as the semantic limit."""
    return ZehnError("E0802", "the host stack was exhausted: expressions or values are nested too deeply",
                     "runtime", blame="callee", fix_hint=HINTS["E0802"])


def run_guarded(fn, depth=DEFAULT_DEPTH):
    """Run fn() on a thread whose stack and Python recursion limit fit `depth` nested Zehn calls.
    Exceptions propagate to the caller. If the thread cannot be created, run in place."""
    box = {}

    def target():
        try:
            box["v"] = fn()
        except BaseException as ex:      # re-raised below, on the caller's thread
            box["e"] = ex

    old_limit, old_stack = sys.getrecursionlimit(), threading.stack_size()
    sys.setrecursionlimit(max(old_limit, depth * 40 + 10_000))
    try:
        threading.stack_size(min(max(64 << 20, depth * (32 << 10)), 1 << 30))
        th = threading.Thread(target=target)
        th.start()
        th.join()
    except (ValueError, RuntimeError):
        target()                         # no big stack available: the RecursionError backstop applies
    finally:
        threading.stack_size(old_stack)
        sys.setrecursionlimit(old_limit)
    if "e" in box:
        raise box["e"]
    return box.get("v")


def static_diags(prog, strict=False):
    """Every static pass, in one place, so `check` and `run` can never disagree:
    names/effects/exhaustiveness -> types -> return paths."""
    diags = Checker(prog, strict).run()
    bad = {d["location"].get("fn") for d in diags if d["severity"] == "error"}
    diags += TypeChecker(prog, skip=bad).run()
    diags += ReturnChecker(prog).run()
    return diags


def nesting_error():
    return ZehnError("E0204", "source is nested too deeply to analyze", "parse",
                     fix_hint="split deeply nested expressions or blocks into helper functions")


def analyze(src, strict=False, path=None, fuel=DEFAULT_FUEL, max_depth=DEFAULT_DEPTH, guard=True):
    """parse -> static passes -> canonical/drift -> examples.
    Returns (prog or None, diagnostics, example results)."""
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


def cmd_check(path, as_json, strict, fuel=DEFAULT_FUEL, max_depth=DEFAULT_DEPTH):
    src = open(path, encoding="utf-8").read()
    prog, diags, examples = run_guarded(
        lambda: analyze(src, strict, path, fuel, max_depth, guard=False), max_depth)
    failed = [x for x in examples if x["status"] == "fail"]
    n_err = sum(1 for d in diags if d["severity"] == "error") + len(failed)
    passed = sum(1 for x in examples if x["status"] == "pass")
    if as_json:
        defs = [{k: v for k, v in r.items() if k != "hash"} for r in definition_refs(prog)] if prog else []
        print(json.dumps({"ok": n_err == 0, "diagnostics": diags, "definitions": defs,
                          "examples": {"passed": passed, "failed": len(failed), "results": examples}},
                         ensure_ascii=False, indent=2))
    else:
        for d in diags:
            print(fmt_diag(d))
        for x in failed:
            print(fmt_diag(x["diag"]))
        print("%s: %d error(s), %d example(s) passed, %d failed" %
              ("FAIL" if n_err else "OK", n_err, passed, len(failed)))
    return 1 if n_err else 0


def to_value(j):
    """JSON -> Zehn value. Objects are records, except {"$": "Ctor", "args": [...]} which builds a
    variant (use it for sum types, ok/err/some/none)."""
    if isinstance(j, dict):
        if "$" in j:
            return V(j["$"], tuple(to_value(a) for a in j.get("args", [])))
        return Rec((k, to_value(v)) for k, v in j.items())
    if isinstance(j, list):
        return [to_value(x) for x in j]
    return j


def _opt(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def cmd_run(path, fname, args_json, grant=(), now=None, fuel=DEFAULT_FUEL, max_depth=DEFAULT_DEPTH):
    src = open(path, encoding="utf-8").read()

    def go():
        prog = parse(src)
        errs = [d for d in static_diags(prog) if d["severity"] == "error"]
        if errs:
            print(json.dumps(errs, ensure_ascii=False, indent=2))
            return 1
        if fname not in prog.funcs:
            print(json.dumps({"code": "E0302", "message": "unknown function %r" % fname}))
            return 1
        it = Interp(prog, granted=grant, now=now, fuel=fuel, max_depth=max_depth)
        it.fresh_budget()
        try:
            out = it.call_fn(prog.funcs[fname], [to_value(a) for a in json.loads(args_json)])
        except RecursionError:
            raise host_stack_error()
        print(show(out))
        return 0

    try:
        return run_guarded(go, max_depth)
    except RecursionError:
        raise nesting_error()
    except ZehnError as z:
        print(json.dumps(z.diag, ensure_ascii=False, indent=2))
        return 1


def cmd_fmt(path, write, check):
    src = open(path, encoding="utf-8").read()
    canon = format_program(parse(src))
    if check:
        if canon != src:
            print("not canonical: %s" % path)
            return 1
        return 0
    if write:
        if canon != src:
            open(path, "w", encoding="utf-8").write(canon)
        return 0
    sys.stdout.write(canon)
    return 0


def cmd_hash(path, as_json):
    refs = definition_refs(parse(open(path, encoding="utf-8").read()))
    if as_json:
        print(json.dumps([{k: v for k, v in r.items() if k != "hash"} for r in refs],
                         ensure_ascii=False, indent=2))
    else:
        for r in refs:
            print("%-14s %s" % (r["ref"], r["name"]))
    return 0


def cmd_lock(path):
    prog = parse(open(path, encoding="utf-8").read())
    with open(lock_path(path), "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "functions": lock_data(prog)}, fh, ensure_ascii=False, indent=2,
                  sort_keys=True)
        fh.write("\n")
    print("locked %d intent(s) in %s" % (len(lock_data(prog)), lock_path(path)))
    return 0


def _perr(code, msg, **extra):
    d = {"code": code, "severity": "error", "phase": "patch", "message": msg}
    d.update(extra)
    return d


def cmd_patch(path, argv):
    """zehn patch <file> replace <ref> --with <file|->   |   delete <ref>   |   insert --with <file|->
    Dry run prints the patched source; --write applies it only when the result has no errors."""
    verb = argv[0] if argv else ""
    src = open(path, encoding="utf-8").read()
    prog = parse(src)
    chunks = [list(c) for c in Fmt(prog, comments=True).chunks()]
    refs = definition_refs(prog)
    by_pos = [i for i, c in enumerate(chunks) if c[0] != "tail"]
    ref_of = {pos: r for pos, r in zip(by_pos, refs)}
    new_text = None
    if verb in ("replace", "insert"):
        w = _opt(argv, "--with")
        if w is None:
            print(json.dumps(_perr("E0703", "%s needs --with <file|->" % verb), ensure_ascii=False))
            return 1
        new_src = sys.stdin.read() if w == "-" else open(w, encoding="utf-8").read()
        try:
            np_ = parse(new_src)
        except ZehnError as z:
            print(json.dumps(z.diag, ensure_ascii=False, indent=2))
            return 1
        if len(np_.order) != 1:
            print(json.dumps(_perr("E0703", "--with must contain exactly one definition, found %d"
                                   % len(np_.order)), ensure_ascii=False))
            return 1
        new_text = Fmt(np_, comments=True).chunks()[0]
    target = None
    if verb in ("replace", "delete"):
        if len(argv) < 2 or "#" not in argv[1]:
            print(json.dumps(_perr("E0701", "%s needs a ref like fn#a3f9" % verb), ensure_ascii=False))
            return 1
        kind, _, h = argv[1].partition("#")
        hits = [p for p, r in ref_of.items() if r["kind"] == kind and r["hash"].startswith(h.lower())]
        have = [r["ref"] for r in refs]
        if not hits or len(h) < 4:
            print(json.dumps(_perr("E0701", "no definition matches %s; it may have changed since you "
                                   "read the file" % argv[1], current_refs=have,
                                   fix_hint="run `zehn hash` and use a current ref"),
                             ensure_ascii=False, indent=2))
            return 1
        if len(hits) > 1:
            print(json.dumps(_perr("E0702", "ref %s is ambiguous" % argv[1],
                                   candidates=[ref_of[p]["ref"] for p in hits],
                                   fix_hint="use a longer hash prefix"), ensure_ascii=False, indent=2))
            return 1
        target = hits[0]
        if verb == "replace" and new_text[0] != kind:
            print(json.dumps(_perr("E0703", "cannot replace a %s with a %s" % (kind, new_text[0])),
                             ensure_ascii=False))
            return 1
    if verb == "replace":
        chunks[target] = list(new_text)
    elif verb == "delete":
        del chunks[target]
    elif verb == "insert":
        at = by_pos[-1] + 1 if by_pos else 0
        chunks.insert(at, list(new_text))
    else:
        print(__doc__)
        return 2
    out = "\n\n".join(c[2] for c in chunks) + "\n"
    prog2, diags, examples = analyze(out, False, None)
    failed = [x for x in examples if x["status"] == "fail"]
    errors = [d for d in diags if d["severity"] == "error"] + [x["diag"] for x in failed]
    if "--write" in argv and not errors:
        open(path, "w", encoding="utf-8").write(out)
        refs2 = definition_refs(prog2)
        print("patched %s; refs now: %s" % (path, ", ".join(r["ref"] for r in refs2)))
        return 0
    if "--write" not in argv:
        sys.stdout.write(out)
    for d in errors:
        sys.stderr.write(fmt_diag(d) + "\n")
    if errors and "--write" in argv:
        sys.stderr.write("not written: the patched program has %d error(s)\n" % len(errors))
    return 1 if errors else 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    try:
        fuel = int(_opt(argv, "--fuel", DEFAULT_FUEL))
        depth = int(_opt(argv, "--max-depth", DEFAULT_DEPTH))
        if cmd == "check":
            return cmd_check(argv[2], "--json" in argv, "--strict" in argv, fuel, depth)
        if cmd == "run" and len(argv) >= 5:
            grant = [g for g in (_opt(argv, "--grant", "") or "").split(",") if g]
            now = _opt(argv, "--now")
            return cmd_run(argv[2], argv[3], argv[4], grant, int(now) if now is not None else None,
                           fuel, depth)
        if cmd == "fmt":
            return cmd_fmt(argv[2], "--write" in argv, "--check" in argv)
        if cmd == "hash":
            return cmd_hash(argv[2], "--json" in argv)
        if cmd == "lock":
            return cmd_lock(argv[2])
        if cmd == "patch" and len(argv) >= 4:
            return cmd_patch(argv[2], argv[3:])
        if cmd == "explain":
            print(EXPLAIN.get(argv[2], "unknown code"))
            return 0
    except ZehnError as z:
        print(json.dumps(z.diag, ensure_ascii=False, indent=2))
        return 1
    except ValueError as ex:             # a non-numeric --fuel / --max-depth / --now
        print(json.dumps({"code": "E0001", "severity": "error", "phase": "usage",
                          "message": "bad option value: %s" % ex}, ensure_ascii=False, indent=2))
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
