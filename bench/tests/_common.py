from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
ROOT = os.path.dirname(BENCH)
DEMO_ROOT = os.path.join(BENCH, "tasks", "_demo")
DEMO_DIR = os.path.join(DEMO_ROOT, "demo_000")
FIXTURES = os.path.join(HERE, "fixtures", "core")
if BENCH not in sys.path:
    sys.path.insert(0, BENCH)


def read(*parts: str) -> str:
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()
