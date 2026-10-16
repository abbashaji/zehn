"""zehnlib.dialect: named experiment flags for A/B runs (`--dialect name=value`).

A module that wants a switch registers it with `flag(...)` and reads it with `get(...)`; the CLI and
`analyze` set values for the duration of one call with `using(...)`. State is process-wide, not
thread-local, because analysis runs on a helper thread (run_guarded). No flag exists yet.
"""
from __future__ import annotations

from contextlib import contextmanager

from zehnlib.errors import ZehnError

_FLAGS = {}      # name -> (default, choices, doc)
_VALUES = {}     # name -> value set by `using` (absent = default)


def _bad(msg, **extra):
    return ZehnError("E0001", msg, "usage", **extra)


def flag(name: str, default: str, choices: tuple, doc: str) -> None:
    """Register the flag `name` with its default, its allowed values and a one-line doc."""
    choices = tuple(choices)
    if name in _FLAGS:
        raise ValueError("dialect flag %r is already registered" % name)
    if not name or "=" in name or any(c.isspace() for c in name):
        raise ValueError("bad dialect flag name %r" % name)
    if default not in choices:
        raise ValueError("default %r of flag %r is not one of %r" % (default, name, choices))
    _FLAGS[name] = (default, choices, doc)


def get(name: str) -> str:
    """Current value of a registered flag (KeyError for an unregistered name: that is a bug)."""
    if name not in _FLAGS:
        raise KeyError("unknown dialect flag %r" % name)
    return _VALUES.get(name, _FLAGS[name][0])


def active() -> dict:
    """Every registered flag with its current value (a copy)."""
    return {n: _VALUES.get(n, d) for n, (d, _c, _doc) in _FLAGS.items()}


def _validate(values):
    for name, value in values.items():
        if name not in _FLAGS:
            raise _bad("unknown dialect flag %r" % name, fix_hint="known flags: %s"
                       % (", ".join(sorted(_FLAGS)) or "none"))
        if value not in _FLAGS[name][1]:
            raise _bad("bad value %r for dialect flag %r" % (value, name),
                       fix_hint="choices: %s" % ", ".join(_FLAGS[name][1]))


@contextmanager
def using(values: dict):
    """Set flags for the duration of the block; validates first, restores the old state always."""
    values = dict(values or {})
    _validate(values)
    saved = dict(_VALUES)
    _VALUES.update(values)
    try:
        yield
    finally:
        _VALUES.clear()
        _VALUES.update(saved)


def parse_cli(items: list) -> dict:
    """["a=b", ...] -> {"a": "b"}. A malformed item, an unknown flag or a bad value raises
    ZehnError("E0001") (the CLI turns that into exit code 2, like any bad option)."""
    out = {}
    for item in items:
        name, eq, value = item.partition("=")
        if not eq or not name:
            raise _bad("--dialect expects name=value, got %r" % item)
        out[name] = value
    _validate(out)
    return out
