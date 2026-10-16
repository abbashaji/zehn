"""Golden safety net: pins the observable behaviour of every program in examples/ and errors/.

One golden file per program and command: tests/golden/<examples|errors>/<program>/<command>.json
  check, check_strict, fmt, hash   stdout + exit code of the CLI (JSON stdout is stored parsed)
  fuel                             fuel used per example (Interp.used), the cost model is language semantics

Every key named "schema" is deleted (recursively) before comparing, so a later task may add one.

Regenerate (only entries you legitimately change):
    python3 tests/test_golden.py --regen                 # everything
    python3 tests/test_golden.py --regen shapes inventory  # only those programs
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import zehn  # noqa: E402

GOLDEN = os.path.join(ROOT, "tests", "golden")
FOLDERS = ("examples", "errors")
CLI = {
    "check": ["check", "--json"],
    "check_strict": ["check", "--json", "--strict"],
    "fmt": ["fmt"],
    "hash": ["hash", "--json"],
}


def programs():
    out = []
    for folder in FOLDERS:
        for name in sorted(os.listdir(os.path.join(ROOT, folder))):
            if name.endswith(".zehn"):
                out.append((folder, name[: -len(".zehn")]))
    return out


def strip_schema(x):
    if isinstance(x, dict):
        return {k: strip_schema(v) for k, v in x.items() if k != "schema"}
    if isinstance(x, list):
        return [strip_schema(v) for v in x]
    return x


def run_cli(folder, name, cmd):
    rel = "%s/%s.zehn" % (folder, name)
    argv = [cmd[0], rel] + cmd[1:]
    p = subprocess.run([sys.executable, os.path.join(ROOT, "zehn.py")] + argv, cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    out = p.stdout
    if "--json" in cmd:
        out = json.loads(out)
    return {"exit": p.returncode, "stdout": out}


class _Metered(zehn.Interp):
    """Interp that remembers the fuel spent by every entry point (one example each)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.spent = []
        self._open = False

    def fresh_budget(self):
        if self._open:
            self.spent.append(self.used)
        self._open = True
        super().fresh_budget()

    def finish(self):
        if self._open:
            self.spent.append(self.used)
            self._open = False


def fuel_per_example(folder, name):
    with open(os.path.join(ROOT, folder, name + ".zehn"), encoding="utf-8") as fh:
        src = fh.read()
    try:
        prog = zehn.parse(src)
    except zehn.ZehnError as z:
        return {"parse_error": z.diag["code"]}
    it = _Metered(prog)
    try:
        results = zehn.run_guarded(it.run_examples)   # as analyze() does: depth limit, not host stack
    except (zehn.ZehnError, RecursionError) as z:
        return {"aborted": type(z).__name__, "spent": it.spent}
    it.finish()
    return {"examples": [{"fn": r["fn"], "line": r["line"], "status": r["status"], "fuel": u}
                         for r, u in zip(results, it.spent)]}


def compute(folder, name, command):
    if command == "fuel":
        return fuel_per_example(folder, name)
    return run_cli(folder, name, CLI[command])


def golden_path(folder, name, command):
    return os.path.join(GOLDEN, folder, name, command + ".json")


def regen(only=()):
    for folder, name in programs():
        if only and name not in only:
            continue
        for command in list(CLI) + ["fuel"]:
            path = golden_path(folder, name, command)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(compute(folder, name, command), fh, ensure_ascii=False, indent=2, sort_keys=True)
                fh.write("\n")


class Golden(unittest.TestCase):
    def test_every_program_has_goldens(self):
        for folder, name in programs():
            for command in list(CLI) + ["fuel"]:
                self.assertTrue(os.path.exists(golden_path(folder, name, command)),
                                "missing golden %s/%s/%s" % (folder, name, command))

    def test_goldens(self):
        for folder, name in programs():
            for command in list(CLI) + ["fuel"]:
                with self.subTest(program="%s/%s" % (folder, name), command=command):
                    with open(golden_path(folder, name, command), encoding="utf-8") as fh:
                        want = strip_schema(json.load(fh))
                    got = strip_schema(json.loads(json.dumps(compute(folder, name, command))))
                    self.assertEqual(want, got)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--regen":
        regen(set(sys.argv[2:]))
    else:
        unittest.main()
