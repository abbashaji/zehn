from __future__ import annotations


def cell_position(cell: int, width: int) -> str:
    row = cell // width
    return str(row) + "," + str(cell - row * width)
