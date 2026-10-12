from __future__ import annotations

from typing import List


def log_long_words(words: List[str], min_len: int) -> int:
    count = 0
    for word in words:
        if len(word) >= min_len:
            print(f"LONG: {word}")
            count += 1
    return count
