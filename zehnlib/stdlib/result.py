"""result.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.errors import ZehnError
from zehnlib.stdlib import builtin
from zehnlib.values import V, show


@builtin("result.is_ok", "(Result<A, E>) -> Bool")
def _is_ok(it, r):
    return r.name == "ok"


@builtin("result.is_err", "(Result<A, E>) -> Bool")
def _is_err(it, r):
    return r.name == "err"


@builtin("result.unwrap", "(Result<A, E>) -> A")
def _unwrap(it, r):
    if isinstance(r, V) and r.name == "ok":
        return r.args[0]
    raise ZehnError("E0507", "result.unwrap applied to %s" % show(r), "runtime")


@builtin("result.map", "(Result<A, E>, Fn(A) -> B) -> Result<B, E>")
def _map(it, r, f):
    if isinstance(r, V) and r.name == "ok":
        return V("ok", (it.call_value(f, [r.args[0]]),))
    return r


@builtin("result.map_err", "(Result<A, E>, Fn(E) -> F) -> Result<A, F>")
def _map_err(it, r, f):
    if isinstance(r, V) and r.name == "err":
        return V("err", (it.call_value(f, [r.args[0]]),))
    return r
