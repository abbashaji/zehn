"""Pass 300: every path of a body must end in `return` (the v0.3 ReturnChecker)."""
from __future__ import annotations

from zehnlib.passes import static_pass
from zehnlib.returns import ReturnChecker


@static_pass(300, "returns")
def returns(prog, strict, prior):
    return ReturnChecker(prog).run()
