"""zehnlib.interp: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import sys
from zehnlib.errors import DEFAULT_DEPTH, DEFAULT_FUEL, HINTS, Return, ZehnError, host_stack_error, run_guarded
from zehnlib.values import FnRef, Rec, Tup, UNIT, V, eq, show
from zehnlib.nodes import N, unparse
from zehnlib.stdlib import BUILTINS, COSTS, EFFECTS, NAMESPACES, NONE, _size
from zehnlib.passes.effect_examples import returns_unit


# ----------------------------------------------------------------------------
# Interpreter
# ----------------------------------------------------------------------------


class MockHost:
    """The fake host of one mocked example (dialect effect_examples=mock): per effect the listed
    results (consumed in order by the effect's functions), and the texts passed to console.print.
    Functions that return Unit consume nothing. Nothing here touches the real host."""

    def __init__(self, results):
        self.results = {eff: list(vals) for eff, vals in results.items()}
        self.printed = []

    def call(self, it, full, eff, args, line):
        if full == "console.print":
            self.printed.append(args[0])
        if returns_unit(full):
            return UNIT
        left = self.results.get(eff, [])
        if not left:
            raise ZehnError("E0606", "%s was called more often than the mock list of effect %r holds results"
                            % (full, eff), "runtime", blame="caller",
                            location={"fn": it.stack[-1] if it.stack else None, "line": line},
                            fix_hint="add more results to `with %s = mock [...]`" % eff)
        return left.pop(0)


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
        self.mock = None              # MockHost while a mocked example runs, else None

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
        if eff not in self.granted and self.mock is None:    # a mocked example never needs a grant
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
        if k == "ptuple":
            if not (isinstance(v, Tup) and len(v.items) == len(p.items)):
                return None
            out = {}
            for sp, sv in zip(p.items, v.items):
                b = self.pmatch(sp, sv)
                if b is None:
                    return None
                out.update(b)
            return out
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
        if k == "tuple":
            return Tup(tuple(self.eval(i, env) for i in e.items))
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
            cost = COSTS.get(full, "flat")
            if cost == "linear":
                self.tick(e.line, sum(_size(a) for a in args))
            elif cost != "flat":
                charges = cost(tuple(args))
                for c in ((charges,) if isinstance(charges, int) else charges):
                    self.tick(e.line, c)
            if full in EFFECTS:
                self.need(EFFECTS[full], full, e.line)
                if self.mock is not None:
                    return self.mock.call(self, full, EFFECTS[full], args, e.line)
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
    def mock_host(self, ex):
        """Evaluate the mock lists of example `ex` (charged like any expression) -> {effect: results}."""
        return {eff: self.eval(lst, {}) for eff, lst, _line in ex.mocks}

    def run_mocked(self, ex, rec_values):
        """Run an example that has mock clauses or `prints`. Returns True when it passes; fills
        `rec_values` (shown in the E0401 diagnostic) with the printed texts when they were asserted."""
        results = self.mock_host(ex)
        expected = self.eval(ex.prints, {}) if ex.prints is not None else None
        host = MockHost(results)
        self.mock = host
        try:
            value = self.eval(ex.expr, {})
        finally:
            self.mock = None
        ok = value is True or (isinstance(value, V) and value.name == "unit")
        if ok and expected is not None and not eq(host.printed, expected):
            ok = False
            rec_values.update({"printed": show(host.printed), "expected printed": show(expected)})
        if not ok:
            self.mock = MockHost(results)      # replay for the left/right values of the diagnostic
        return ok

    def run_examples(self):
        results = []
        for f in self.p.funcs.values():
            for ex in f.examples:
                rec = {"fn": f.name, "line": ex.line, "example": ex.text}
                self.fresh_budget()
                try:
                    mocked = bool(getattr(ex, "mocks", None)) or getattr(ex, "prints", None) is not None
                    extra = {}
                    ok = self.run_mocked(ex, extra) if mocked else self.eval(ex.expr, {})
                    if ok is True:
                        rec["status"] = "pass"
                    else:
                        rec["status"] = "fail"
                        values = dict(self.explain(ex.expr, {}), **extra)
                        rec["diag"] = {
                            "code": "E0401", "severity": "error", "phase": "runtime",
                            "message": "example is not true",
                            "location": {"fn": f.name, "line": ex.line, "clause": "example " + ex.text},
                            "values": values, "fix_hint": HINTS["E0401"]}
                except (ZehnError, RecursionError) as z:
                    if isinstance(z, RecursionError):
                        z = host_stack_error()
                    rec["status"] = "fail"
                    z.diag.setdefault("location", {})
                    z.diag["via_example"] = {"fn": f.name, "line": ex.line, "text": ex.text}
                    rec["diag"] = z.diag
                finally:
                    self.mock = None
                results.append(rec)
        return results
