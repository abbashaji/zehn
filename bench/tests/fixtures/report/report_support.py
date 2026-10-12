from __future__ import annotations

import os
import sys

FIXTURES = os.path.dirname(os.path.abspath(__file__))
HERE = os.path.dirname(os.path.dirname(FIXTURES))
BENCH = os.path.dirname(HERE)
REPORT_PY = os.path.join(BENCH, "report.py")

if BENCH not in sys.path:
    sys.path.insert(0, BENCH)


def fixture(name):
    return os.path.join(FIXTURES, name)


def rec(task="t1", lang="zehn", variant="default", model="m1", repeat=1, first=True,
        accepted=1, final=True, rounds=None, tin=100, tout=50):
    if rounds is None:
        rounds = [{"i": 1, "tool_ok": True, "diag_codes": [], "unknown_names": 0,
                   "in_tokens": tin, "out_tokens": tout}]
    return {
        "schema": 1, "run_id": "r", "set": "dev", "task_id": task, "category": "c",
        "kind": "write", "lang": lang, "variant": variant, "model": model,
        "repeat": repeat, "temperature": 0.2, "rounds": rounds, "accepted_round": accepted,
        "first_try_pass": first, "final_pass": final,
        "final_tests": {"passed": 5 if final else 0, "total": 5},
        "total_in_tokens": tin, "total_out_tokens": tout, "wall_ms": 1, "error": None,
    }
