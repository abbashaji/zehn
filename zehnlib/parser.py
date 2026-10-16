"""zehnlib.parser: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

from zehnlib.errors import ZehnError
from zehnlib.lexer import tokenize
from zehnlib.nodes import N, Program, mock_on


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
            line = self.cur[2]
            self.i += 1
            if self.at_op(")"):
                raise self.tuple_size_error("type", line)
            ts = [self.type_()]
            while self.at_op(","):
                self.i += 1
                ts.append(self.type_())
            self.eat("OP", ")")
            if len(ts) < 2:
                raise self.tuple_size_error("type", line)
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

    def tuple_size_error(self, what, line):
        """E0318: a tuple needs two or more elements (`()`, `(x,)` and `(T)` as a type)."""
        return ZehnError("E0318", "a tuple %s needs two or more elements; there is no empty or "
                         "one-element tuple" % what, "parse", location={"line": line},
                         fix_hint="write at least two elements, or drop the parentheses around a "
                                  "single one")

    def clause(self):
        kw = self.cur
        self.i += 1
        first = self.cur
        e = self.expr()
        last = self.t[self.i - 1]
        text = self.src[first[3]:last[4]]
        self.eol()
        return N("clause", kw[2], expr=e, text=text)

    def example_clause(self):
        """`example E` and, under the dialect `effect_examples=mock`, an optional tail:
        { with <effect> = mock [<results>] } [ prints [<texts>] ]. Without the flag the tail is
        not recognised, so `with` is simply an unexpected token (E0201)."""
        kw = self.cur
        self.i += 1
        first = self.cur
        e = self.expr()
        mocks, prints = [], None
        if mock_on():
            while self.at("ID", "with"):
                wline = self.cur[2]
                self.i += 1
                eff = self.eat("ID")[1]
                while self.at_op("."):
                    self.i += 1
                    eff += "." + self.eat("ID")[1]
                self.eat("OP", "=")
                if not self.at("ID", "mock"):
                    self.err("'mock'")
                self.i += 1
                if not self.at_op("["):
                    self.err("'['")
                mocks.append((eff, self.primary(), wline))
            if self.at("ID", "prints"):
                self.i += 1
                if not self.at_op("["):
                    self.err("'['")
                prints = self.primary()
        last = self.t[self.i - 1]
        text = self.src[first[3]:last[4]]
        self.eol()
        return N("clause", kw[2], expr=e, text=text, mocks=mocks, prints=prints)

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
                examples.append(self.example_clause())
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
            if self.at_op("("):
                raise ZehnError("E0316", "`%s` cannot take a tuple pattern; there is no destructuring "
                                "`%s`" % (c[1], c[1]), "parse", location={"line": self.cur[2]},
                                fix_hint="bind the tuple to a name and take it apart with "
                                         "`match t do case (a, b) => ... end match`")
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
        if self.at_op("("):
            self.i += 1
            if self.at_op(")"):
                raise self.tuple_size_error("pattern", line)
            items = [self.pattern()]
            while self.at_op(","):
                self.i += 1
                if self.at_op(")"):
                    raise self.tuple_size_error("pattern", line)
                items.append(self.pattern())
            self.eat("OP", ")")
            if len(items) < 2:
                raise self.tuple_size_error("pattern", line)
            return N("ptuple", line, items=items)
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
                if self.at("INT"):
                    raise ZehnError("E0317", "a tuple element cannot be read by position (`.%d`)"
                                    % self.cur[1], "parse", location={"line": line},
                                    fix_hint="take the tuple apart with `match t do case (a, b) => "
                                             "... end match`")
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
            if self.at_op(")"):
                raise self.tuple_size_error("expression", line)
            e = self.expr()
            if not self.at_op(","):
                self.eat("OP", ")")
                return e
            items = [e]
            while self.at_op(","):
                self.i += 1
                if self.at_op(")"):
                    raise self.tuple_size_error("expression", line)
                items.append(self.expr())
            self.eat("OP", ")")
            return N("tuple", line, items=items)
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
