from __future__ import annotations


def countdown(start: int, step: int) -> int:
    if step <= 0:
        print(f"bad step: {step}")
        return 0
    printed = 0
    value = start
    while value > 0:
        print(f"T-minus {value}")
        printed += 1
        value -= step
    print("liftoff")
    return printed
