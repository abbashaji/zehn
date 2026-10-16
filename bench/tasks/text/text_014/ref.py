from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def wrap_words(body: str, width: int) -> Result[str]:
    if width < 1:
        return Err("width must be positive")
    lines: List[str] = []
    line = ""
    for word in body.split(" "):
        if word == "":
            continue
        if line == "":
            line = word
        elif len(line) + 1 + len(word) <= width:
            line = line + " " + word
        else:
            lines.append(line)
            line = word
    if line != "":
        lines.append(line)
    return Ok("|".join(lines))
