"""Adapter contract: one adapter per compared language. Stdlib only, Python 3.9+."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

# A diagnostic is {"code": str, "message": str, "line": int | None, "unknown_name": bool, "raw": str}.
# `unknown_name` is True when the tool says a function, type, variable or effect does not exist
# (this feeds the hallucination-rate metric).


class Adapter:
    name = ""   # "zehn" | "python_plain" | "python_strict" | "ts_strict" | "rust" | "rust_strict"
    ext = ""    # ".zehn" | ".py" | ".ts" | ".rs"

    def available(self) -> Tuple[bool, str]:
        """(True, "") if every external tool this adapter needs is installed, else (False, reason)."""
        raise NotImplementedError

    def system_prompt(self, task: Dict[str, Any]) -> str:
        """Language primer shown to the model (the Zehn adapter returns SPEC.md plus the tool protocol)."""
        raise NotImplementedError

    def tool_check(self, task: Dict[str, Any], code: str, workdir: str) -> Dict[str, Any]:
        """The feedback tool the model sees. Returns
        {"ok": bool, "diagnostics": List[diagnostic], "tool_ms": int}.
        `ok` means the tool accepts the program (it says nothing about hidden tests)."""
        raise NotImplementedError

    def run_hidden(self, task: Dict[str, Any], code: str, tests: List[Dict[str, Any]],
                   workdir: str) -> Dict[str, Any]:
        """Run the hidden tests. Returns
        {"passed": int, "total": int, "failures": [{"index": int, "got": str, "want": str}], "ms": int}.
        A program that does not build or crashes scores passed=0."""
        raise NotImplementedError
