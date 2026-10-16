from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Cmd:
    op: str
    n: int


def run_stack(cmds: List[Cmd]) -> Result[int]:
    stack: List[int] = []
    for pos, cmd in enumerate(cmds, start=1):
        if cmd.op == "push":
            stack.append(cmd.n)
        elif cmd.op in ("pop", "dup", "add", "mul", "swap"):
            needed = 1 if cmd.op in ("pop", "dup") else 2
            if len(stack) < needed:
                return Err(f"stack underflow at command {pos}")
            if cmd.op == "pop":
                stack.pop()
            elif cmd.op == "dup":
                stack.append(stack[-1])
            else:
                top = stack.pop()
                below = stack.pop()
                if cmd.op == "add":
                    stack.append(below + top)
                elif cmd.op == "mul":
                    stack.append(below * top)
                else:
                    stack.append(top)
                    stack.append(below)
        else:
            return Err(f"unknown op at command {pos}")
        print(f"{pos}: [{','.join(str(x) for x in stack)}]")
    if not stack:
        return Err("empty stack at end")
    return Ok(stack[-1])
