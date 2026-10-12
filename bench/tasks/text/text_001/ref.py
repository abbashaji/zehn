from __future__ import annotations


def csv_field_count(line: str) -> int:
    if line == "":
        return 0
    return len(line.split(","))
