from __future__ import annotations

from typing import List


def number_lines(body: str) -> str:
    out: List[str] = []
    n = 0
    for line in body.split("\n"):
        if line == "":
            out.append("")
        else:
            n += 1
            out.append(str(n) + ". " + line)
    return "\n".join(out)
