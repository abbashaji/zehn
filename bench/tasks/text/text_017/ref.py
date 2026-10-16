from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def max_tag_depth(markup: str) -> Result[int]:
    open_tags: List[str] = []
    deepest = 0
    for piece in markup.split("<")[1:]:
        tag = piece.split(">")[0]
        if tag.startswith("/"):
            name = tag[1:]
            if not open_tags:
                return Err("unexpected closing tag: " + name)
            top = open_tags[-1]
            if top != name:
                return Err("mismatched tag: expected " + top + ", found " + name)
            open_tags.pop()
        else:
            open_tags.append(tag)
            deepest = max(deepest, len(open_tags))
    if open_tags:
        return Err("unclosed tag: " + open_tags[-1])
    return Ok(deepest)
