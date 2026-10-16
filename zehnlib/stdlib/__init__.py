"""zehnlib.stdlib: the standard-library registry.

One module per namespace (list_, text, int_, option, result, map_, console, time_). A module
registers each function with the `builtin` decorator; `zehnlib.discover` imports every module of
this package, so a new namespace is a new file and no shared file is edited.

The registries are plain module-level dicts / sets, mutated in place, so `from zehnlib.stdlib
import BUILTINS` stays valid after later registrations.
"""
from __future__ import annotations

from zehnlib.types import instantiate
from zehnlib.values import MapV, V

BUILTINS = {}      # "ns.fn" -> impl(it, *args)
SIGS = {}          # "ns.fn" -> signature string (same syntax as v0.3)
COSTS = {}         # "ns.fn" -> "flat" | "linear" | callable(args: tuple) -> int | tuple of int
EFFECTS = {}       # "ns.fn" -> effect name
NAMESPACES = set()
CTORS = {"ok", "err", "some", "none"}
RESERVED = set(CTORS) | {"out"}     # NAMESPACES | CTORS | {"out"}, grown with NAMESPACES

NONE = V("none")


def _size(v):
    if isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return v.bit_length() >> 6
    if isinstance(v, (list, str)):
        return len(v)
    if isinstance(v, MapV):
        return len(v.items)
    return 0


def builtin(name: str, sig: str, *, cost="flat", effect=None):
    """Register `impl(it, *args)` as the stdlib function `name` ("ns.fn").

    cost: "flat"   no charge beyond the one step every expression costs;
          "linear" charge sum(_size(a) for a in args);
          callable f(args: tuple) returning an int or a tuple of ints, each ticked separately in order.
    effect: the effect name the caller must declare in `uses` (and the host must grant), or None.
    A duplicate name raises ValueError."""
    ns, dot, fn = name.partition(".")
    if not dot or not ns or not fn or "." in fn:
        raise ValueError("stdlib name %r must look like 'namespace.function'" % name)
    if name in BUILTINS:
        raise ValueError("stdlib function %r is already registered" % name)
    if ns in CTORS or ns == "out":
        raise ValueError("namespace %r is reserved" % ns)
    if not (cost in ("flat", "linear") or callable(cost)):
        raise ValueError("cost of %r must be 'flat', 'linear' or a callable, got %r" % (name, cost))
    if effect is not None and not isinstance(effect, str):
        raise ValueError("effect of %r must be a name or None, got %r" % (name, effect))
    try:
        instantiate(sig)
    except (ValueError, IndexError) as ex:
        raise ValueError("bad signature for %r: %s" % (name, ex))

    def register(impl):
        BUILTINS[name] = impl
        SIGS[name] = sig
        COSTS[name] = cost
        if effect is not None:
            EFFECTS[name] = effect
        NAMESPACES.add(ns)
        RESERVED.add(ns)
        return impl

    return register
