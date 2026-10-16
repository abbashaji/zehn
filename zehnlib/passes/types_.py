"""Pass 200: static types (the v0.3 TypeChecker). Functions that already have errors are skipped,
so one mistake does not cascade."""
from __future__ import annotations

from zehnlib.passes import static_pass
from zehnlib.typecheck import TypeChecker


@static_pass(200, "types")
def types(prog, strict, prior):
    bad = {d.get("location", {}).get("fn") for d in prior if d["severity"] == "error"}
    return TypeChecker(prog, skip=bad).run()
