"""int.* functions (moved from the v0.3 stdlib tables, bodies unchanged)."""
from __future__ import annotations

from zehnlib.stdlib import _size, builtin


# Two charges, in this order (ADR-0007): linear in the size of the number, then the schoolbook
# cost of converting it to decimal.
@builtin("int.to_text", "(Int) -> Text",
         cost=lambda a: (_size(a[0]), (_size(a[0]) + 1) ** 2 // 4))
def _to_text(it, n):
    return str(n)


@builtin("int.abs", "(Int) -> Int")
def _abs(it, n):
    return abs(n)


@builtin("int.min", "(Int, Int) -> Int")
def _min(it, a, b):
    return min(a, b)


@builtin("int.max", "(Int, Int) -> Int")
def _max(it, a, b):
    return max(a, b)


# Explicit division (TASK_06c). Fuel matches the operators `/` and `%` in Interp.binop: the one
# step of the expression itself, plus wa * wb words when an operand is above 128 bits, charged
# before the work (and before the zero-divisor check, as the operators do).
def _div_cost(args):
    a, b = args
    if isinstance(a, int) and isinstance(b, int) and (a.bit_length() > 128 or b.bit_length() > 128):
        return ((a.bit_length() >> 6) + 1) * ((b.bit_length() >> 6) + 1)
    return ()


def _zero_divisor(it):
    from zehnlib.errors import ZehnError
    return ZehnError("E0505", "division by zero", "runtime", location={"line": it.line},
                     blame="caller", fix_hint="guard with `requires b != 0`")


@builtin("int.div_floor", "(Int, Int) -> Int", cost=_div_cost)
def _div_floor(it, a, b):
    if b == 0:
        raise _zero_divisor(it)
    return a // b


@builtin("int.div_trunc", "(Int, Int) -> Int", cost=_div_cost)
def _div_trunc(it, a, b):
    if b == 0:
        raise _zero_divisor(it)
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


@builtin("int.rem_euclid", "(Int, Int) -> Int", cost=_div_cost)
def _rem_euclid(it, a, b):
    if b == 0:
        raise _zero_divisor(it)
    return a % abs(b)
