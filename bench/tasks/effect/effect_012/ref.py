from __future__ import annotations

from typing import Dict, List, Tuple

MOVES: Dict[Tuple[str, str], str] = {
    ("closed", "open"): "open",
    ("open", "close"): "closed",
    ("closed", "lock"): "locked",
    ("locked", "unlock"): "closed",
}


def run_door(events: List[str]) -> str:
    state = "closed"
    for event in events:
        moved = MOVES.get((state, event))
        if moved is None:
            print(f"ignored {event} in {state}")
        else:
            print(f"{state} -> {moved}")
            state = moved
    return state
