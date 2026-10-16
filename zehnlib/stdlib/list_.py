"""list.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.stdlib import NONE, builtin
from zehnlib.values import V, eq


@builtin("list.len", "(List<A>) -> Int")
def _len(it, xs):
    return len(xs)


@builtin("list.get", "(List<A>, Int) -> Option<A>")
def _get(it, xs, i):
    return V("some", (xs[i],)) if 0 <= i < len(xs) else NONE


@builtin("list.append", "(List<A>, A) -> List<A>", cost="linear")
def _append(it, xs, x):
    return xs + [x]


@builtin("list.concat", "(List<A>, List<A>) -> List<A>", cost="linear")
def _concat(it, a, b):
    return a + b


@builtin("list.contains", "(List<A>, A) -> Bool", cost="linear")
def _contains(it, xs, x):
    return any(eq(x, y) for y in xs)


@builtin("list.sum", "(List<Int>) -> Int", cost="linear")
def _sum(it, xs):
    return sum(xs)


@builtin("list.map", "(List<A>, Fn(A) -> B) -> List<B>", cost="linear")
def _map(it, xs, f):
    return [it.call_value(f, [x]) for x in xs]


@builtin("list.filter", "(List<A>, Fn(A) -> Bool) -> List<A>", cost="linear")
def _filter(it, xs, f):
    return [x for x in xs if it.call_value(f, [x]) is True]


@builtin("list.fold", "(List<A>, B, Fn(B, A) -> B) -> B", cost="linear")
def _fold(it, xs, init, f):
    acc = init
    for x in xs:
        acc = it.call_value(f, [acc, x])
    return acc
