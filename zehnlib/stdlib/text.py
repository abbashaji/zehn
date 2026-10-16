"""text.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.stdlib import builtin


@builtin("text.len", "(Text) -> Int")
def _len(it, t):
    return len(t)


@builtin("text.concat", "(Text, Text) -> Text", cost="linear")
def _concat(it, a, b):
    return a + b


@builtin("text.split_on", "(Text, Text) -> List<Text>", cost="linear")
def _split_on(it, t, sep):
    return t.split(sep)


@builtin("text.contains", "(Text, Text) -> Bool", cost="linear")
def _contains(it, t, s):
    return s in t


@builtin("text.to_upper", "(Text) -> Text", cost="linear")
def _to_upper(it, t):
    return t.upper()
