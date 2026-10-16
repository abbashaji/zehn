from __future__ import annotations

from typing import Dict, List

from bench_prelude import Err, Ok, Result

NEEDS: Dict[str, int] = {"push": 0, "dup": 1, "drop": 1, "swap": 2, "add": 2, "sub": 2, "mul": 2}


def run_machine(ops: List[str], args: List[int]) -> Result[int]:
    if len(ops) != len(args):
        return Err("length mismatch")
    stack: List[int] = []
    for i, (op, arg) in enumerate(zip(ops, args)):
        need = NEEDS.get(op)
        if need is None:
            return Err("unknown op at " + str(i))
        if len(stack) < need:
            return Err("stack underflow at " + str(i))
        if op == "push":
            stack.append(arg)
        elif op == "dup":
            stack.append(stack[-1])
        elif op == "drop":
            stack.pop()
        else:
            y = stack.pop()
            x = stack.pop()
            if op == "swap":
                stack.append(y)
                stack.append(x)
            elif op == "add":
                stack.append(x + y)
            elif op == "sub":
                stack.append(x - y)
            else:
                stack.append(x * y)
    if not stack:
        return Err("empty stack")
    return Ok(stack[-1])
