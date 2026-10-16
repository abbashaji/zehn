"""console.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.stdlib import builtin
from zehnlib.values import UNIT


@builtin("console.print", "(Text) -> Unit", effect="console")
def _print(it, t):
    it.stdout.write(t + "\n")
    return UNIT
