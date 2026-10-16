"""zehnlib.nodes: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

from zehnlib import dialect


def mock_on():
    """True when the dialect flag `effect_examples` is `mock` (mocked effect examples, ADR-0019)."""
    return dialect.get("effect_examples") == "mock"

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


def walk(n):
    """Yield `n` and every N reachable from it, pre-order, each node once.

    Children are the N values found in `n.__dict__`, directly or inside lists, tuples and dict
    values (recursively), in field order. Nothing here knows a node kind, so a new kind needs no
    change. Iterative, so a deeply nested tree cannot exhaust the host stack."""
    seen = set()
    todo = [n]
    while todo:
        cur = todo.pop()
        if id(cur) in seen:
            continue
        seen.add(id(cur))
        yield cur
        kids = []
        _children(cur.__dict__.values(), kids)
        todo.extend(reversed(kids))


def _children(values, out):
    for v in values:
        if isinstance(v, N):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            _children(v, out)
        elif isinstance(v, dict):
            _children(v.values(), out)


def unparse(n):
    if n.k == "name":
        return n.id
    if n.k == "field":
        o = unparse(n.obj)
        return o + "." + n.name if o else None
    return None
