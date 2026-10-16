"""Pass 100: names, arity, mutability, effects, exhaustiveness (the v0.3 Checker)."""
from __future__ import annotations

from zehnlib.checker import Checker
from zehnlib.passes import static_pass


@static_pass(100, "names")
def names(prog, strict, prior):
    return Checker(prog, strict).run()
