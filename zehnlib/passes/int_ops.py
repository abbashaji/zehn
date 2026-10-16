"""Pass 410 (TASK_06c): dialect flag `int_ops`. Under `explicit`, the operators `/` and `%` are an
error (E0312) and Int division is written with int.div_floor, int.div_trunc or int.rem_euclid.
Under `operators` (the default) the pass reports nothing."""
from __future__ import annotations

from zehnlib import dialect
from zehnlib.errors import explain
from zehnlib.nodes import walk
from zehnlib.passes import static_pass

dialect.flag("int_ops", "operators", ("operators", "explicit"),
             "Int division: `operators` allows `/` and `%` (floor semantics); `explicit` forbids "
             "them and requires int.div_floor, int.div_trunc, int.rem_euclid")

explain("E0312", "Dialect int_ops=explicit: the operators `/` and `%` are not allowed on Int. "
                 "Use int.div_floor(a, b) (floor division, same as `/` today), int.div_trunc(a, b) "
                 "(division truncating toward zero) or int.rem_euclid(a, b) (remainder with "
                 "0 <= r < |b|). A zero divisor is still E0505. There is no explicit name for the "
                 "floor remainder `%`; for a positive divisor int.rem_euclid gives the same value.")

_HINT = ("use int.div_floor(a, b), int.div_trunc(a, b) or int.rem_euclid(a, b); "
         "`/` is int.div_floor, and `%` is int.rem_euclid when the divisor is positive")


@static_pass(410, "int_ops")
def int_ops(prog, strict, prior):
    if dialect.get("int_ops") != "explicit":
        return []
    out = []
    for f in prog.funcs.values():
        for n in walk(f):
            if n.k == "bin" and n.op in ("/", "%"):
                out.append({"code": "E0312", "severity": "error", "phase": "check",
                            "message": "the operator `%s` on Int is not allowed under int_ops=explicit"
                                       % n.op,
                            "location": {"fn": f.name, "line": n.line},
                            "fix_hint": _HINT})
    out.sort(key=lambda d: (d["location"]["line"], d["message"]))
    return out
