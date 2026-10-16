from __future__ import annotations

from typing import Dict, List, Tuple

from bench_prelude import Err, Ok, Result

STATUSES = ["new", "paid", "packed", "shipped", "delivered", "cancelled", "refunded"]
EVENTS = ["pay", "pack", "ship", "deliver", "cancel", "refund"]
TRANSITIONS: Dict[Tuple[str, str], str] = {
    ("new", "pay"): "paid",
    ("paid", "pack"): "packed",
    ("packed", "ship"): "shipped",
    ("shipped", "deliver"): "delivered",
    ("new", "cancel"): "cancelled",
    ("paid", "cancel"): "cancelled",
    ("packed", "cancel"): "cancelled",
    ("delivered", "refund"): "refunded",
}


def apply_events(status: str, events: List[str]) -> Result[str]:
    if status not in STATUSES:
        return Err("unknown status: " + status)
    current = status
    for step, event in enumerate(events, start=1):
        if event not in EVENTS:
            return Err("step %d: unknown event %s" % (step, event))
        following = TRANSITIONS.get((current, event))
        if following is None:
            return Err("step %d: cannot %s when %s" % (step, event, current))
        current = following
    return Ok(current)
