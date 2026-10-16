"""zehn explain: the long text for a diagnostic code."""
from __future__ import annotations

from zehnlib.cli import command
from zehnlib.errors import EXPLAIN


@command("explain", "explain <code>")
def explain(argv):
    print(EXPLAIN.get(argv[0], "unknown code"))
    return 0
