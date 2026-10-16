"""zehnlib.returns: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

from zehnlib.fmt import fmt_pattern


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
