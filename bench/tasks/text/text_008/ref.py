from __future__ import annotations

from typing import List


def contains_all(content: str, keywords: List[str]) -> bool:
    upper = content.upper()
    for keyword in keywords:
        if keyword.upper() not in upper:
            return False
    return True
