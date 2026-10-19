"""zehnlib.checker: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import difflib
from zehnlib.nodes import N
from zehnlib.values import show
from zehnlib.stdlib import BUILTINS, CTORS, EFFECTS, NAMESPACES, RESERVED


# ----------------------------------------------------------------------------
# Static checker
# ----------------------------------------------------------------------------


_WILD = N("pwild", 0)


class Checker:
    def __init__(self, prog, strict=False):
        self.p, self.strict, self.diags = prog, strict, []
        self.f = None
        self.in_contract = False
        self.mocked = False           # inside the expression of an example that has mock clauses
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
            self.mocked = bool(getattr(cl, "mocks", None))     # effectful calls are mocked, not E0602
            self.expr(cl.expr, {})
            self.mocked = False
            for _eff, lst, _line in getattr(cl, "mocks", None) or ():
                self.expr(lst, {})                              # mock results are pure
            if getattr(cl, "prints", None) is not None:
                self.expr(cl.prints, {})
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
            if f.uses:
                # ADR-0019 (outcome of the A/B, option B): an effectful function cannot be called from an
                # example (E0602), so neither `--strict` (E0402) nor W0101 asks one of it.
                pass
            elif self.strict:
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
        elif p.k == "ptuple":
            for a in p.items:
                self.pbinds(a, sc)
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

    @staticmethod
    def irrefutable(p):
        """A pattern that matches every value of its type: `_`, a name, or a tuple of those."""
        if p.k in ("pwild", "pbind"):
            return True
        return p.k == "ptuple" and all(Checker.irrefutable(a) for a in p.items)

    def exhaustive(self, s):
        pats = [p for p, _, _ in s.cases]
        if any(p.k in ("pwild", "pbind") for p in pats):
            return
        if any(p.k == "ptuple" for p in pats):
            self.exhaustive_tuples(s, pats)
            return
        variants = [p for p in pats if p.k == "pvariant"]
        lits = [p for p in pats if p.k == "plit"]
        covered = {p.name for p in variants if all(self.irrefutable(a) for a in p.args)}
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

    # -- exhaustiveness of a match that has tuple patterns (TASK_07) --
    def exhaustive_tuples(self, s, pats):
        """Matrix check over the whole pattern tree. The names pass knows no types, so the
        constructors of a column come from the patterns themselves (a sum type from its
        declaration, `ok`/`err`, `some`/`none`, `true`/`false`; Int and Text literals never cover
        everything). Returns quietly when the patterns are inconsistent: the type checker reports
        those (E0313, E0315, E0306, E0302, E0303)."""
        w = self.witness([[p] for p in pats], 1)
        if w:
            self.d("E0301", "non-exhaustive match: missing %s" % w[0], s.line,
                   fix_hint="add the missing case(s) or `case _ =>`")

    def witness(self, rows, n):
        """A list of n texts describing values that no row matches, or None when the rows cover
        every value (or cannot be judged). Each row is a list of n patterns."""
        if n == 0:
            return None if rows else []
        heads = [r[0] for r in rows if r[0].k not in ("pwild", "pbind")]
        if not heads:
            w = self.witness([r[1:] for r in rows], n - 1)
            return None if w is None else ["_"] + w
        kinds = {h.k for h in heads}
        if kinds == {"ptuple"}:
            arity = {len(h.items) for h in heads}
            if len(arity) != 1:
                return None
            k = arity.pop()
            sub = [(r[0].items if r[0].k == "ptuple" else [_WILD] * k) + r[1:] for r in rows]
            w = self.witness(sub, k + n - 1)
            return None if w is None else ["(" + ", ".join(w[:k]) + ")"] + w[k:]
        if kinds == {"pvariant"}:
            names = {h.name for h in heads}
            if names <= {"ok", "err"}:
                family = [("ok", 1), ("err", 1)]
            elif names <= {"some", "none"}:
                family = [("some", 1), ("none", 0)]
            else:
                t = self.p.variants.get(sorted(names)[0])
                if not t or not names <= {vn for vn, _ in self.p.types[t[0]]["variants"]}:
                    return None
                family = [(vn, self.p.variants[vn][1]) for vn, _ in self.p.types[t[0]]["variants"]]
            if any(len(h.args) != dict(family)[h.name] for h in heads):
                return None
            for name, arity in family:
                sub = [(r[0].args if r[0].k == "pvariant" and r[0].name == name else
                        [_WILD] * arity) + r[1:]
                       for r in rows if r[0].k != "pvariant" or r[0].name == name]
                w = self.witness(sub, arity + n - 1)
                if w is not None:
                    shown = name if not arity else "%s(%s)" % (name, ", ".join(w[:arity]))
                    return [shown] + w[arity:]
            return None
        if kinds == {"plit"}:
            vals = [h.v for h in heads]
            if all(isinstance(v, bool) for v in vals):
                for b in (True, False):
                    sub = [r[1:] for r in rows if r[0].k not in ("plit",) or r[0].v is b]
                    w = self.witness(sub, n - 1)
                    if w is not None:
                        return [show(b)] + w
                return None
            if any(isinstance(v, bool) for v in vals):
                return None
            w = self.witness([r[1:] for r in rows if r[0].k != "plit"], n - 1)
            return None if w is None else ["_"] + w
        return None

    def record_builtin(self, full, eff, line):
        if self.in_contract:
            self.d("E0602", "contracts and examples must be pure, but %s needs effect %r"
                   % (full, eff), line)
        else:
            self.body_effects.append((full, eff, line))

    def record_call(self, callee, line):
        if self.in_contract:
            if callee.uses and not self.mocked:
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
                    if full in EFFECTS:
                        self.record_builtin(full, EFFECTS[full], e.line)
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
        elif k in ("list", "tuple"):
            for i in e.items:
                self.expr(i, sc)
        elif k == "record":
            for _, v in e.fields:
                self.expr(v, sc)
