from __future__ import annotations


def replace_all(source: str, pattern: str, replacement: str) -> str:
    if pattern == "":
        return source
    return replacement.join(source.split(pattern))
