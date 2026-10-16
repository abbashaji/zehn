"""map.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.stdlib import NONE, builtin
from zehnlib.values import MapV, V


@builtin("map.empty", "() -> Map<K, V>")
def _empty(it):
    return MapV()


@builtin("map.set", "(Map<K, V>, K, V) -> Map<K, V>", cost="linear")
def _set(it, m, k, v):
    return m.set(k, v)


@builtin("map.get", "(Map<K, V>, K) -> Option<V>", cost="linear")
def _get(it, m, k):
    return (lambda i: V("some", (m.items[i][1],)) if i >= 0 else NONE)(m.find(k))


@builtin("map.has", "(Map<K, V>, K) -> Bool", cost="linear")
def _has(it, m, k):
    return m.find(k) >= 0


@builtin("map.remove", "(Map<K, V>, K) -> Map<K, V>", cost="linear")
def _remove(it, m, k):
    return m.remove(k)


@builtin("map.keys", "(Map<K, V>) -> List<K>", cost="linear")
def _keys(it, m):
    return [k for k, _ in m.items]


@builtin("map.values", "(Map<K, V>) -> List<V>", cost="linear")
def _values(it, m):
    return [v for _, v in m.items]


@builtin("map.len", "(Map<K, V>) -> Int")
def _len(it, m):
    return len(m.items)
