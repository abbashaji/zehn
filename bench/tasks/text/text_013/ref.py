from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bench_prelude import Err, Ok, Result


@dataclass
class Binding:
    key: str
    value: str


def _lookup(bindings: List[Binding], key: str) -> Optional[str]:
    for b in bindings:
        if b.key == key:
            return b.value
    return None


def fill_template(template: str, bindings: List[Binding]) -> Result[str]:
    parts = template.split("{")
    out = parts[0]
    for piece in parts[1:]:
        halves = piece.split("}")
        if len(halves) != 2:
            return Err("unclosed placeholder")
        value = _lookup(bindings, halves[0])
        if value is None:
            return Err("unknown placeholder: " + halves[0])
        out += value + halves[1]
    return Ok(out)
