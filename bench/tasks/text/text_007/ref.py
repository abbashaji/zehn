from __future__ import annotations


def longest_word(line: str) -> int:
    best = 0
    for word in line.split(" "):
        best = max(best, len(word))
    return best
