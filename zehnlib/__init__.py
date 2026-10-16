"""The Zehn reference implementation, split out of the old single-file zehn.py.

Core modules (each only imports from the ones before it): errors, explain_text, values, lexer,
nodes, parser, types, dialect, stdlib (package), fmt, checker, returns, typecheck, interp,
passes (package), analysis, cli, commands (package).

Three folders are registries filled by discovery: a new module dropped into `stdlib/`, `passes/`
or `commands/` is imported on `import zehnlib` and registers itself; no shared file is edited.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)   # Int is arbitrary precision; fuel (not Python) bounds its size


def discover(package):
    """Import every submodule of `package` in sorted-name order and return the modules.

    Importing is the registration: a module registers its functions, passes or commands with the
    decorators of its registry at import time. Importing twice is a no-op (sys.modules)."""
    names = sorted(m.name for m in pkgutil.iter_modules(package.__path__))
    return [importlib.import_module("%s.%s" % (package.__name__, n)) for n in names]


# Order matters only in that the registries' own modules are imported by their package __init__
# before any member module runs; passes and commands import the core modules they need themselves.
from zehnlib import commands, passes, stdlib   # noqa: E402

discover(stdlib)
discover(passes)
discover(commands)
