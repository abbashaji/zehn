"""Zehn adapter: `zehn.py check --json --strict` as the feedback tool, the project's interpreter for tests."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple

from .base import Adapter

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
VARIANTS_DIR = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "variants")
CHECK_TIMEOUT = 60
RUN_TIMEOUT = 120

_PROTOCOL = """\

## How your work is checked

You write one complete Zehn program that defines the requested function (you may add helper
functions). Reply with the complete program in a single fenced code block. The program is then
checked with `zehn check --json --strict`: types, effects, return paths, contracts, canonical
layout, and the program's own `example` lines (in strict mode every function needs at least one
`example`). If the check fails you receive its JSON diagnostics and reply with a corrected, complete
program. Hidden tests then call the requested function; your program is judged by them.
"""


class ZehnAdapter(Adapter):
    name = "zehn"
    ext = ".zehn"
    external_tools: List[str] = []

    def __init__(self) -> None:
        self.root = PROJECT_ROOT
        self.variant: List[Tuple[str, str]] = []

    def set_variant(self, pairs: List[Tuple[str, str]]) -> None:
        self.variant = list(pairs)

    def available(self) -> Tuple[bool, str]:
        if not os.path.exists(os.path.join(self.root, "zehn.py")):
            return False, "zehn.py not found at %s" % self.root
        return True, ""

    def _dialect_args(self) -> List[str]:
        out: List[str] = []
        for k, v in self.variant:
            out += ["--dialect", "%s=%s" % (k, v)]
        return out

    def system_prompt(self, task: Dict[str, Any]) -> str:
        with open(os.path.join(self.root, "SPEC.md"), encoding="utf-8") as f:
            text = f.read()
        text += _PROTOCOL
        for k, v in self.variant:
            p = os.path.join(VARIANTS_DIR, "%s=%s.md" % (k, v))
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    text += "\n" + f.read()
        return text

    def _write(self, code: str, workdir: str) -> str:
        path = os.path.join(workdir, "solution.zehn")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        return path

    @staticmethod
    def _diag(d: Dict[str, Any]) -> Dict[str, Any]:
        code = str(d.get("code", "?"))
        loc = d.get("location") if isinstance(d.get("location"), dict) else {}
        line = loc.get("line")
        return {"code": code, "message": str(d.get("message", "")),
                "line": line if isinstance(line, int) else None,
                "unknown_name": code == "E0302", "raw": json.dumps(d, ensure_ascii=False)}

    def tool_check(self, task: Dict[str, Any], code: str, workdir: str) -> Dict[str, Any]:
        path = self._write(code, workdir)
        cmd = [sys.executable, os.path.join(self.root, "zehn.py"), "check", path, "--json", "--strict"]
        cmd += self._dialect_args()
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, timeout=CHECK_TIMEOUT)
        except subprocess.TimeoutExpired:
            return self._fail("TOOL_TIMEOUT", "zehn check did not finish in %ds" % CHECK_TIMEOUT, t0)
        ms = int((time.time() - t0) * 1000)
        try:
            data = json.loads(p.stdout)
        except ValueError:
            return self._fail("TOOL_CRASH", (p.stderr or p.stdout)[-500:], t0)
        if isinstance(data, dict) and "ok" not in data and "code" in data:   # a single raised diagnostic
            return {"ok": False, "diagnostics": [self._diag(data)], "tool_ms": ms}
        if not isinstance(data, dict) or "ok" not in data:
            return self._fail("TOOL_CRASH", p.stdout[-500:], t0)
        diags = [self._diag(d) for d in data.get("diagnostics", []) if isinstance(d, dict)]
        for x in (data.get("examples") or {}).get("results", []):
            if isinstance(x, dict) and x.get("status") == "fail" and isinstance(x.get("diag"), dict):
                diags.append(self._diag(x["diag"]))
        return {"ok": bool(data["ok"]), "diagnostics": diags, "tool_ms": ms}

    @staticmethod
    def _fail(code: str, message: str, t0: float) -> Dict[str, Any]:
        d = {"code": code, "message": message, "line": None, "unknown_name": False, "raw": message}
        return {"ok": False, "diagnostics": [d], "tool_ms": int((time.time() - t0) * 1000)}

    def run_hidden(self, task: Dict[str, Any], code: str, tests: List[Dict[str, Any]],
                   workdir: str) -> Dict[str, Any]:
        total = len(tests)
        t0 = time.time()
        path = self._write(code, workdir)
        spec_path = os.path.join(workdir, "spec.json")
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump({"entry": task["entry"], "console": "console" in task["effects"], "cases": tests}, f)
        cmd = [sys.executable, os.path.join(_HERE, "_zehn_runner.py"), self.root, path, spec_path]
        try:
            p = subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, timeout=RUN_TIMEOUT)
            data = json.loads(p.stdout)
        except (subprocess.TimeoutExpired, ValueError):
            return {"passed": 0, "total": total, "failures": [], "ms": int((time.time() - t0) * 1000)}
        failures: List[Dict[str, Any]] = []
        passed = 0
        if data.get("stage") != "ok":
            return {"passed": 0, "total": total, "ms": int((time.time() - t0) * 1000),
                    "failures": [{"index": -1, "got": str(data.get("error")), "want": data.get("stage", "")}]}
        for i, r in enumerate(data["results"]):
            if r["ok"]:
                passed += 1
            else:
                failures.append({"index": i, "got": r["error"] or r["got"], "want": r["want"]})
        return {"passed": passed, "total": total, "failures": failures, "ms": int((time.time() - t0) * 1000)}
