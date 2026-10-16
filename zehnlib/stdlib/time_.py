"""time.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.stdlib import builtin


@builtin("time.now", "() -> Int", effect="time.now")
def _now(it):
    return it.clock()
