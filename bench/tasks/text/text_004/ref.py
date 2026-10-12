from __future__ import annotations

from typing import Optional


def lookup_value(config: str, key: str) -> Optional[str]:
    for entry in config.split(";"):
        parts = entry.split("=")
        if len(parts) == 2 and parts[0] == key:
            return parts[1]
    return None
