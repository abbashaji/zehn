"""zehnlib.errors: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import sys
import threading


# Deterministic resource limits (SPEC section 13). Both are properties of the *program's*
# semantics, not of the host machine, so a run that exhausts them does so identically everywhere.
DEFAULT_FUEL = 1_000_000      # steps per entry point (one example, or one `run` call)
DEFAULT_DEPTH = 10_000        # nested Zehn calls

# ----------------------------------------------------------------------------
# Diagnostics
# ----------------------------------------------------------------------------


class ZehnError(Exception):
    def __init__(self, code, message, phase, **extra):
        super().__init__(message)
        self.diag = {"code": code, "severity": "error", "phase": phase, "message": message}
        self.diag.update(extra)


class Return(Exception):
    def __init__(self, value):
        self.value = value


HINTS = {}
EXPLAIN = {}


def hint(code, text):
    """Register the fix hint attached to runtime diagnostics with this code."""
    if code in HINTS:
        raise ValueError("hint for %s is already registered" % code)
    HINTS[code] = text


def explain(code, text):
    """Register the `zehn explain <code>` text."""
    if code in EXPLAIN:
        raise ValueError("explain text for %s is already registered" % code)
    EXPLAIN[code] = text


def host_stack_error():
    """Backstop: the host's own stack ran out before the semantic depth limit did (this needs
    pathologically nested *expressions*, not deep recursion). Same code as the semantic limit."""
    return ZehnError("E0802", "the host stack was exhausted: expressions or values are nested too deeply",
                     "runtime", blame="callee", fix_hint=HINTS["E0802"])


def run_guarded(fn, depth=DEFAULT_DEPTH):
    """Run fn() on a thread whose stack and Python recursion limit fit `depth` nested Zehn calls.
    Exceptions propagate to the caller. If the thread cannot be created, run in place."""
    box = {}

    def target():
        try:
            box["v"] = fn()
        except BaseException as ex:      # re-raised below, on the caller's thread
            box["e"] = ex

    old_limit, old_stack = sys.getrecursionlimit(), threading.stack_size()
    sys.setrecursionlimit(max(old_limit, depth * 40 + 10_000))
    try:
        threading.stack_size(min(max(64 << 20, depth * (32 << 10)), 1 << 30))
        th = threading.Thread(target=target)
        th.start()
        th.join()
    except (ValueError, RuntimeError):
        target()                         # no big stack available: the RecursionError backstop applies
    finally:
        threading.stack_size(old_stack)
        sys.setrecursionlimit(old_limit)
    if "e" in box:
        raise box["e"]
    return box.get("v")


import zehnlib.explain_text  # noqa: E402,F401  (fills EXPLAIN and HINTS; last, after explain/hint exist)
