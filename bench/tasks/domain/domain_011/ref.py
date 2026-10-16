from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bench_prelude import Err, Ok, Result


@dataclass
class Rule:
    role: str
    action: str
    allow: bool


def _first_applying(rules: List[Rule], roles: List[str], action: str, allow: bool) -> Optional[Rule]:
    for rule in rules:
        if rule.allow == allow and rule.role in roles and rule.action in (action, "*"):
            return rule
    return None


def check_access(rules: List[Rule], roles: List[str], action: str) -> Result[str]:
    if action == "":
        return Err("action required")
    denied = _first_applying(rules, roles, action, False)
    if denied is not None:
        return Err("denied by role " + denied.role)
    granted = _first_applying(rules, roles, action, True)
    if granted is not None:
        return Ok("allowed by role " + granted.role)
    return Err("no rule for " + action)
