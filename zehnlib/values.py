"""zehnlib.values: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import json
from dataclasses import dataclass


# ----------------------------------------------------------------------------
# Values
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class V:
    name: str
    args: tuple = ()


class Rec(dict):
    pass


@dataclass(frozen=True)
class Tup:
    """An immutable tuple of two or more values (TASK_07). A class of its own, so it can never be
    confused with a list or with the Python tuples used inside V and MapV."""
    items: tuple


@dataclass(frozen=True)
class FnRef:
    name: str


class MapV:
    """Immutable insertion-ordered map. Updating an existing key keeps its position."""
    __slots__ = ("items",)

    def __init__(self, items=()):
        self.items = tuple(items)

    def find(self, k):
        for i, (a, _) in enumerate(self.items):
            if eq(a, k):
                return i
        return -1

    def set(self, k, v):
        i = self.find(k)
        if i < 0:
            return MapV(self.items + ((k, v),))
        return MapV(self.items[:i] + ((self.items[i][0], v),) + self.items[i + 1:])

    def remove(self, k):
        i = self.find(k)
        return self if i < 0 else MapV(self.items[:i] + self.items[i + 1:])


UNIT = V("unit")


def eq(a, b):
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, V) and isinstance(b, V):
        return (a.name == b.name and len(a.args) == len(b.args)
                and all(eq(x, y) for x, y in zip(a.args, b.args)))
    if isinstance(a, Tup) and isinstance(b, Tup):
        return len(a.items) == len(b.items) and all(eq(x, y) for x, y in zip(a.items, b.items))
    if isinstance(a, Rec) and isinstance(b, Rec):
        return a.keys() == b.keys() and all(eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(eq(x, y) for x, y in zip(a, b))
    if isinstance(a, MapV) and isinstance(b, MapV):
        if len(a.items) != len(b.items):
            return False
        for k, v in a.items:
            i = b.find(k)
            if i < 0 or not eq(v, b.items[i][1]):
                return False
        return True
    return a == b


def show(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, V):
        return v.name if not v.args else "%s(%s)" % (v.name, ", ".join(show(a) for a in v.args))
    if isinstance(v, Tup):
        return "(" + ", ".join(show(x) for x in v.items) + ")"
    if isinstance(v, Rec):
        return "{" + ", ".join("%s: %s" % (k, show(x)) for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(show(x) for x in v) + "]"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, FnRef):
        return "<fn %s>" % v.name
    if isinstance(v, MapV):
        return "map{" + ", ".join("%s: %s" % (show(k), show(x)) for k, x in v.items) + "}"
    return str(v)
