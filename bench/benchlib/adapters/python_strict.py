"""Python adapter, strict: the plain checks plus `mypy --strict` and `ruff check`."""
from __future__ import annotations

import json
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from .python_plain import PythonPlainAdapter

_MYPY_LINE = re.compile(r"^(?P<file>[^:\n]+):(?P<line>\d+):(?:\d+:)? (?P<sev>error|warning|note): "
                        r"(?P<msg>.*?)(?:  \[(?P<code>[\w-]+)\])?$")
_MYPY_UNKNOWN = ("name-defined", "attr-defined")
TOOL_TIMEOUT = 120


class PythonStrictAdapter(PythonPlainAdapter):
    name = "python_strict"
    external_tools = ["mypy", "ruff"]
    strict = True

    def available(self) -> Tuple[bool, str]:
        missing = [t for t in self.external_tools if self.tool_command(t) is None]
        if missing:
            return False, "missing tool(s): %s (pip install %s)" % (", ".join(missing), " ".join(missing))
        return True, ""

    def system_prompt(self, task: Dict[str, Any]) -> str:
        from .python_plain import python_primer
        return python_primer() + (
            "Checks: the program is byte-compiled, imported, and the visible examples are run; then\n"
            "`mypy --strict` and `ruff check` must both pass with no findings.\n")

    def _strict_diags(self, workdir: str) -> List[Dict[str, Any]]:
        return self._mypy(workdir) + self._ruff(workdir)

    def _exec(self, cmd: List[str], workdir: str) -> Optional["subprocess.CompletedProcess[str]"]:
        try:
            return subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True, timeout=TOOL_TIMEOUT)
        except (subprocess.TimeoutExpired, OSError):
            return None

    def _mypy(self, workdir: str) -> List[Dict[str, Any]]:
        base = self.tool_command("mypy")
        assert base is not None
        p = self._exec(base + ["--strict", "--no-color-output", "--no-error-summary", "--show-error-codes",
                               "--cache-dir", "/dev/null", "solution.py"], workdir)
        if p is None:
            return [self._d("mypy-timeout", "mypy did not finish", None)]
        out: List[Dict[str, Any]] = []
        for line in p.stdout.splitlines():
            m = _MYPY_LINE.match(line)
            if m and m.group("sev") == "error":
                code = m.group("code") or "mypy"
                out.append(self._d(code, m.group("msg"), int(m.group("line")), code in _MYPY_UNKNOWN, line))
        if not out and p.returncode not in (0, 1):
            out.append(self._d("mypy-crash", (p.stderr or p.stdout)[-300:], None))
        return out

    def _ruff(self, workdir: str) -> List[Dict[str, Any]]:
        base = self.tool_command("ruff")
        assert base is not None
        p = self._exec(base + ["check", "--isolated", "--no-cache", "--select", "E4,E7,E9,F",
                               "--output-format", "json", "solution.py"], workdir)
        if p is None:
            return [self._d("ruff-timeout", "ruff did not finish", None)]
        try:
            items = json.loads(p.stdout or "[]")
        except ValueError:
            return [self._d("ruff-crash", (p.stderr or p.stdout)[-300:], None)]
        out = []
        for it in items:
            code = it.get("code") or "syntax-error"
            row = (it.get("location") or {}).get("row")
            out.append(self._d(code, str(it.get("message", "")), row if isinstance(row, int) else None,
                               code == "F821", json.dumps(it)))
        return out
