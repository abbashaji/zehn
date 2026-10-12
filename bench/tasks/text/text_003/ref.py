from __future__ import annotations


def count_word(sentence: str, word: str) -> int:
    count = 0
    for token in sentence.split(" "):
        if token == word:
            count += 1
    return count
