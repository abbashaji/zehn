"""Pass 400: E0311, unconditional recursion.

A cycle in the call graph in which every edge is a call that is *certainly executed* whenever the
caller runs up to its statement. Such a function can never reach a result, so the pass reports it
before any example runs. The contract is zero false positives: when it is unsure whether a call
is certain, the call is not counted (the run-time fuel and depth limits catch what this misses).

Counted calls (an edge f -> g, `g` a top-level function):
  - in a straight-line statement of the body (`let`, `var`, `:=`, expression, `return`);
  - inside an argument of such a call, or inside any operand of an operator other than
    `and` / `or` / `implies`;
  - in the condition of an `if` or the subject of a `match`;
and only while nothing earlier can leave the body: no `return` and no `?` before the call, in the
same expression (evaluation order: arguments left to right, then the callee) or in an earlier
statement (an `if` or `match` that contains either one also ends the certain part).

Not counted: anything inside an `if` branch or a `match` case, the right operand of `and`, `or`,
`implies`, anything after a `?` or a `return`, `requires` / `ensures` / `example` clauses, a
function name used as a value (`list.map(xs, g)`), a call with the wrong number of arguments, and
a name that a parameter, `let`, `var` or pattern binding of the same function hides.
"""
from __future__ import annotations

from zehnlib.errors import explain
from zehnlib.nodes import walk
from zehnlib.passes import static_pass

MAX_CYCLES = 200        # safety valve for pathological graphs; real programs have a handful

_SHORT_CIRCUIT = ("and", "or", "implies")
_EXITS = ("return", "try")


explain("E0311", "Unconditional recursion: a function calls itself, or a group of functions call "
                 "each other in a cycle, and no call in the cycle sits under an `if`, a `match` "
                 "case or the right side of `and` / `or` / `implies`. Whenever the function runs "
                 "to that call it makes it, so it can never return. `cycle` lists the functions in "
                 "call order with the line of the call that leads to the next. Put the recursive "
                 "call in a branch and add a base case that returns without recursing. The check "
                 "is deliberately conservative: it never flags a function that can terminate, but "
                 "it misses some endless recursion (the fuel and depth limits catch those at "
                 "run time).")


def _has_exit(nodes) -> bool:
    """True if any `return` statement or `?` occurs in these nodes (a node or a list of them)."""
    for top in (nodes if isinstance(nodes, list) else [nodes]):
        for n in walk(top):
            if n.k in _EXITS:
                return True
    return False


def _locals(fn) -> set:
    """Every name that can hide a top-level function inside `fn`."""
    names = {p[0] for p in fn.params}
    for n in walk(fn):
        if n.k in ("let", "var", "pbind"):
            names.add(n.name)
    return names


class _Scan:
    def __init__(self, prog, fn):
        self.prog, self.fn, self.hidden = prog, fn, _locals(fn)
        self.edges = {}     # callee name -> line of the first certain call

    # -- expressions: return whether control certainly reaches what follows --
    def ex(self, e, live):
        if not live:
            return False
        k = e.k
        if k in ("int", "str", "bool", "name", "ctor"):
            return True
        if k == "list":
            for i in e.items:
                live = self.ex(i, live)
            return live
        if k == "record":
            for _name, v in e.fields:
                live = self.ex(v, live)
            return live
        if k == "field":
            return self.ex(e.obj, live)
        if k in ("neg", "not"):
            return self.ex(e.expr, live)
        if k == "try":
            self.ex(e.expr, live)
            return False
        if k == "bin":
            live = self.ex(e.l, live)
            if e.op in _SHORT_CIRCUIT:
                return live and not _has_exit(e.r)
            return self.ex(e.r, live)
        if k == "call":
            for a in e.args:
                live = self.ex(a, live)
            f = e.fn
            if f.k == "name":
                g = self.prog.funcs.get(f.id)
                if (live and g is not None and f.id not in self.hidden
                        and len(g.params) == len(e.args)):
                    self.edges.setdefault(f.id, e.line)
                return live
            if f.k == "ctor":
                return live
            return self.ex(f, live)
        return False        # a node kind this pass does not know: nothing after it is certain

    # -- statements --
    def block(self, stmts):
        live = True
        for s in stmts:
            k = s.k
            if k in ("let", "var", "assign", "expr"):
                live = self.ex(s.expr, live)
            elif k == "return":
                self.ex(s.expr, live)
                live = False
            elif k == "if":
                live = self.ex(s.cond, live) and not _has_exit(list(s.then) + list(s.els))
            elif k == "match":
                live = self.ex(s.subject, live) and not _has_exit(
                    [stmt for _pat, body, _line in s.cases for stmt in body])
            else:
                live = False
            if not live:
                break
        return self.edges


def call_graph(prog) -> dict:
    """{fn name: {callee name: line of the first certain call}} for every top-level function."""
    return {name: _Scan(prog, f).block(f.body) for name, f in prog.funcs.items()}


def cycles(graph, order) -> list:
    """Every elementary cycle once, as a list of function names, starting at its function that
    comes first in `order` and following the edges in the order they appear."""
    rank = {n: i for i, n in enumerate(order)}
    found = []
    for start in order:
        stack = [(start, iter(graph.get(start, {})))]
        path = [start]
        while stack and len(found) < MAX_CYCLES:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop()
                path.pop()
            elif nxt == start:
                found.append(list(path))
            elif nxt in rank and rank[nxt] > rank[start] and nxt not in path:
                path.append(nxt)
                stack.append((nxt, iter(graph.get(nxt, {}))))
    return found


@static_pass(400, "recursion")
def recursion(prog, strict, prior):
    graph = call_graph(prog)
    out = []
    for cyc in cycles(graph, list(prog.funcs)):
        steps = [{"fn": f, "line": graph[f][cyc[(i + 1) % len(cyc)]]} for i, f in enumerate(cyc)]
        if len(cyc) == 1:
            msg = "function %r always calls itself (line %d): it can never return" % (
                cyc[0], steps[0]["line"])
        else:
            msg = "functions %s always call each other in a cycle: none of them can ever return" % (
                " -> ".join(repr(f) for f in cyc + [cyc[0]]))
        out.append({
            "code": "E0311", "severity": "error", "phase": "check", "message": msg,
            "location": {"fn": cyc[0], "line": steps[0]["line"]},
            "cycle": steps,
            "fix_hint": "put the recursive call under an `if` or a `match` case and add a base "
                        "case that returns without recursing"})
    return out
