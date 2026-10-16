"""option.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.stdlib import builtin
from zehnlib.values import V


@builtin("option.unwrap_or", "(Option<A>, A) -> A")
def _unwrap_or(it, o, d):
    return o.args[0] if o.name == "some" else d


@builtin("option.is_some", "(Option<A>) -> Bool")
def _is_some(it, o):
    return o.name == "some"


@builtin("option.map", "(Option<A>, Fn(A) -> B) -> Option<B>")
def _map(it, o, f):
    if isinstance(o, V) and o.name == "some":
        return V("some", (it.call_value(f, [o.args[0]]),))
    return o
