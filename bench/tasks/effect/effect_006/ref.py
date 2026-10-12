from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Cmd:
    op: str
    n: int


def run_commands(cmds: List[Cmd]) -> int:
    acc = 0
    for pos, cmd in enumerate(cmds, start=1):
        if cmd.op == "add":
            acc += cmd.n
        elif cmd.op == "sub":
            acc -= cmd.n
        elif cmd.op == "mul":
            acc *= cmd.n
        elif cmd.op == "show":
            print(f"acc = {acc}")
        elif cmd.op == "halt":
            print(f"halted at command {pos}")
            break
        else:
            print(f"command {pos}: unknown op [{cmd.op}]")
    return acc
