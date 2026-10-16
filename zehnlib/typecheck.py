"""zehnlib.typecheck: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import difflib
from zehnlib.stdlib import NAMESPACES, SIGS
from zehnlib.passes.effect_examples import result_kind
from zehnlib.types import BOOL, T_UNIT, GENERIC_ARITY, INT, PRIMS, TCon, TEXT, TFn, TVar, instantiate, parse_type_text, prune, try_unify, unify, unify_probe


def show_t(t):
    """Type text for messages. Same as zehnlib.types.show_t, except that a tuple type is written
    the way the source writes it, `(Int, Text)`, not `Tuple<Int, Text>` (TASK_07)."""
    t = prune(t)
    if isinstance(t, TVar):
        return "_"
    if isinstance(t, TFn):
        return "Fn(%s) -> %s" % (", ".join(show_t(p) for p in t.params), show_t(t.ret))
    if t.name == "Tuple":
        return "(%s)" % ", ".join(show_t(a) for a in t.args)
    if t.args:
        return "%s<%s>" % (t.name, ", ".join(show_t(a) for a in t.args))
    return t.name


def _tuple_arity(t):
    """Number of elements when `t` is a tuple type, else None."""
    t = prune(t)
    return len(t.args) if isinstance(t, TCon) and t.name == "Tuple" else None


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
        wa, ga = _tuple_arity(wp), _tuple_arity(gp)
        if wa is not None and ga is not None and wa != ga:
            self.d("E0314", "tuple has %d element(s) but %d expected%s: expected %s, found %s"
                   % (ga, wa, " in " + ctx if ctx else "", w, g), line, expected=w, found=g,
                   fix_hint="a tuple type is fixed in size: give the tuple exactly %d element(s)" % wa)
            return
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
            if getattr(cl, "mocks", None) or getattr(cl, "prints", None) is not None:
                self.mocked_example(cl)
            else:
                self.expect(cl.expr, BOOL, {}, "example")
        self.block(f.body, dict(sc))

    def mocked_example(self, cl):
        """Example with mock clauses (dialect effect_examples=mock). Its expression is Bool, or Unit
        (a call run only for its effects: it passes when it finishes and `prints` matches). Each mock
        list is typed against the result type of the functions of its effect (E0607); `prints` is a
        List<Text>."""
        got = self.infer(cl.expr, {}, BOOL)
        if not (unify(got, BOOL) or (cl.mocks and unify(got, T_UNIT))):
            self.mismatch(cl.expr.line, BOOL, got, "example")
        for eff, lst, line in cl.mocks:
            kind, want = result_kind(eff)
            if kind == "ok":
                for item in lst.items:
                    t = self.infer(item, {}, want)
                    if not unify(t, want):
                        self.d("E0607", "mock result for effect %r has type %s, expected %s"
                               % (eff, show_t(t), show_t(want)), item.line, expected=show_t(want),
                               found=show_t(t), fix_hint="every result of `%s` has type %s" % (eff, show_t(want)))
            elif lst.items:
                why = {"none": "no stdlib function has the effect %r, so no result can be mocked" % eff,
                       "unit": "effect %r returns Unit, which has no literal: its mock list is empty" % eff,
                       "mixed": "functions of effect %r return different types: its results cannot be listed" % eff}[kind]
                self.d("E0607", why, lst.line, fix_hint="write `with %s = mock []`" % eff)
        if cl.prints is not None:
            self.expect(cl.prints, TCon("List", [TEXT]), {}, "prints")

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
        if k == "ptuple":
            n, tt = len(p.items), prune(t)
            if isinstance(tt, TVar):
                subs = [TVar() for _ in p.items]
                unify(tt, TCon("Tuple", subs))
            elif _tuple_arity(tt) is None:
                self.d("E0315", "tuple pattern of %d elements cannot match a value of type %s"
                       % (n, show_t(tt)), p.line, expected=show_t(tt),
                       found="(%s)" % ", ".join(["_"] * n),
                       fix_hint="a tuple pattern matches only a tuple value; use a pattern for %s"
                                % show_t(tt))
                subs = [TVar() for _ in p.items]
            elif _tuple_arity(tt) != n:
                self.d("E0313", "tuple pattern has %d element(s) but the matched value %s has %d"
                       % (n, show_t(tt), _tuple_arity(tt)), p.line, expected=show_t(tt),
                       found="(%s)" % ", ".join(["_"] * n),
                       fix_hint="write a pattern with exactly %d element(s)" % _tuple_arity(tt))
                subs = [TVar() for _ in p.items]
            else:
                subs = list(tt.args)
            for sp, st in zip(p.items, subs):
                self.pattern(sp, st, sc)
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
        if k == "tuple":
            return self.tuple_(e, sc, exp)
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

    def tuple_(self, e, sc, exp):
        """`(a, b, ...)`: when the expected type is a tuple of the same size, every element is
        checked against its own element type (so a mistake is reported on the element); otherwise
        the elements are inferred and the caller compares the whole type (E0314 for a size
        difference, E0306 for anything else)."""
        want = prune(exp) if exp is not None else None
        if _tuple_arity(want) == len(e.items):
            for i, (item, wt) in enumerate(zip(e.items, want.args)):
                self.expect(item, wt, sc, "tuple element %d" % (i + 1))
            return want
        return TCon("Tuple", [self.infer(item, sc) for item in e.items])

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
