from __future__ import annotations

from typing import List, Optional


def problem(name: str) -> Optional[str]:
    if len(name) < 3:
        return "too short"
    if len(name) > 12:
        return "too long"
    if " " in name:
        return "has space"
    return None


def validate_usernames(names: List[str]) -> int:
    failures = 0
    for pos, name in enumerate(names, start=1):
        reason = problem(name)
        if reason is not None:
            print(f"#{pos} [{name}]: {reason}")
            failures += 1
    return failures
