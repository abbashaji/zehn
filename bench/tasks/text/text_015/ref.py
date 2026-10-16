from __future__ import annotations

from typing import Dict, List


def word_counts(body: str) -> str:
    counts: Dict[str, int] = {}
    for word in body.split(" "):
        if word == "":
            continue
        key = word.upper()
        counts[key] = counts.get(key, 0) + 1
    pieces: List[str] = [key + "=" + str(n) for key, n in counts.items()]
    return ", ".join(pieces)
