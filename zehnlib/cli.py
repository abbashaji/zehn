"""Zehn v0.4 reference interpreter: command-line front end and the command registry.

Parses Zehn source, runs static checks (names, arity, mutability, effects,
exhaustiveness), executes programs, and verifies requires / ensures / example.
Every diagnostic is a machine-readable dict (see SPEC.md section 9).

Each subcommand is a module in zehnlib/commands/ that registers itself with `command`; the
usage lines below are collected from the registry.
"""
from __future__ import annotations

import json
import sys

from zehnlib import dialect
from zehnlib.errors import DEFAULT_DEPTH, DEFAULT_FUEL, ZehnError
from zehnlib.values import Rec, V

COMMANDS = {}      # name -> fn(argv: list) -> int   (argv = the arguments after the subcommand)


def command(name: str, usage: str):
    """Register `fn(argv) -> exit code` as the subcommand `name`. `usage` is its usage line(s),
    without the leading `zehn.py` (continuation lines are separated by newlines)."""
    if name in COMMANDS:
        raise ValueError("command %r is already registered" % name)

    def register(fn):
        fn.usage = usage
        COMMANDS[name] = fn
        return fn

    return register


def usage_text():
    lines = ["Usage:"]
    for name in sorted(COMMANDS):
        for ln in COMMANDS[name].usage.split("\n"):
            lines.append("    zehn.py " + ln)
    return (__doc__.split("\n\nEach subcommand")[0] + "\n\n" + "\n".join(lines))


def usage_error():
    print(usage_text())
    return 2


def to_value(j):
    """JSON -> Zehn value. Objects are records, except {"$": "Ctor", "args": [...]} which builds a
    variant (use it for sum types, ok/err/some/none)."""
    if isinstance(j, dict):
        if "$" in j:
            return V(j["$"], tuple(to_value(a) for a in j.get("args", [])))
        return Rec((k, to_value(v)) for k, v in j.items())
    if isinstance(j, list):
        return [to_value(x) for x in j]
    return j


def _opt(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def dialect_opts(argv):
    """Every `--dialect name=value` (repeatable) -> {name: value}; bad input raises E0001."""
    items = []
    for i, a in enumerate(argv):
        if a == "--dialect":
            if i + 1 >= len(argv):
                raise ZehnError("E0001", "--dialect expects name=value", "usage")
            items.append(argv[i + 1])
    return dialect.parse_cli(items)


def main(argv):
    if len(argv) == 2 and argv[1] in ("--help", "-h"):
        print(usage_text())
        return 0
    if len(argv) < 3:
        return usage_error()
    fn = COMMANDS.get(argv[1])
    try:
        int(_opt(argv, "--fuel", DEFAULT_FUEL))          # validated for every command, as in v0.3
        int(_opt(argv, "--max-depth", DEFAULT_DEPTH))
        if fn is None:
            return usage_error()
        return fn(argv[2:])
    except ZehnError as z:
        print(json.dumps(z.diag, ensure_ascii=False, indent=2))
        return 2 if z.diag["code"] == "E0001" else 1
    except ValueError as ex:             # a non-numeric --fuel / --max-depth / --now
        print(json.dumps({"code": "E0001", "severity": "error", "phase": "usage",
                          "message": "bad option value: %s" % ex}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
