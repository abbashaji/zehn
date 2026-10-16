from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Span:
    lo: int
    hi: int


def merge_spans(spans: List[Span]) -> List[Span]:
    merged: List[Span] = []
    for s in spans:
        if merged and s.lo <= merged[-1].hi:
            merged[-1].hi = max(merged[-1].hi, s.hi)
        else:
            merged.append(Span(s.lo, s.hi))
    return merged
