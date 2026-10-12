"""Scripted models: no network, no key. They read the reference solution from the loop context."""
from __future__ import annotations

from typing import Any, Dict

from . import ModelError

_BROKEN = "fn broken(\n"   # a syntax error in Zehn, Python, TypeScript and Rust alike


def _fence(ext: str, code: str) -> str:
    return "```%s\n%s%s```\n" % (ext.lstrip("."), code, "" if code.endswith("\n") else "\n")


class StubModel:
    BEHAVIOURS = ("perfect", "broken_then_fixed", "never_valid")

    def __init__(self, behaviour: str):
        if behaviour not in self.BEHAVIOURS:
            raise ModelError("unknown stub %r (have %s)" % (behaviour, ", ".join(self.BEHAVIOURS)))
        self.behaviour = behaviour
        self.name = "stub:" + behaviour

    def complete(self, system: str, messages: Any, temperature: float, ctx: Dict[str, Any]) -> Dict[str, Any]:
        ext = ctx["ext"]
        if self.behaviour == "perfect":
            text = _fence(ext, ctx["ref_code"])
        elif self.behaviour == "broken_then_fixed":
            text = _fence(ext, _BROKEN if ctx["round"] == 1 else ctx["ref_code"])
        else:  # never_valid: prose only, so the loop sees no code block at all
            text = "I am not able to write this program."
        return {"text": text, "in_tokens": len(system) // 4 + sum(len(m["content"]) // 4 for m in messages),
                "out_tokens": len(text) // 4}
