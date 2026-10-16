"""zehnlib.passes: the static-pass registry.

A pass is `fn(prog, strict: bool, prior: list) -> list` of diagnostics, where `prior` holds every
diagnostic produced by the passes that ran before it. Passes run in ascending `order`.
v0.3 passes: names (100), types (200), returns (300). Orders 400 to 499 are reserved for new
analyses; each new analysis is one new module in this folder.
"""
from __future__ import annotations

PASSES = []     # [(order, name, fn)], kept sorted by (order, name)


def static_pass(order: int, name: str):
    """Register `fn(prog, strict, prior) -> list` as the static pass `name` at position `order`."""
    if not isinstance(order, int) or isinstance(order, bool):
        raise ValueError("pass order must be an int, got %r" % (order,))
    if any(n == name for _, n, _ in PASSES):
        raise ValueError("static pass %r is already registered" % name)

    def register(fn):
        PASSES.append((order, name, fn))
        PASSES.sort(key=lambda p: (p[0], p[1]))
        return fn

    return register


def run_static(prog, strict=False) -> list:
    """Run every registered pass in ascending order; return all diagnostics in that order."""
    diags = []
    for _order, _name, fn in list(PASSES):
        diags += fn(prog, strict, list(diags))
    return diags
