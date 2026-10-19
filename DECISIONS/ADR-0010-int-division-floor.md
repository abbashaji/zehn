# ADR-0010 `/` and `%` on `Int` use floor semantics (resolved in v0.4 by ADR-0017)
Status: decided (floor kept, now specified; see ADR-0017 for the numbers, underpowered)

## Problem
What `/` and `%` return for negative operands. SPEC invariant 7 requires determinism and no undefined behavior.

## Options
The repository records only the current behaviour. Alternatives, listed here for the v0.4 decision and not recorded as considered earlier: truncate toward zero with `%` taking the sign of the dividend, or Euclidean division with a non-negative remainder.

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None. For reference, the current behaviour: `-7 / 2` gives -4, `-7 % 2` gives 1, `7 / -2` gives -4, `7 % -2` gives -1.

## Decision
Not a deliberate choice: `zehn.py` computes `a // b` and `a % b` with Python semantics. SPEC section 12 records it as a known limit: "deterministic but should be pinned down before v1". Division by zero is `E0505`, blamed on the caller (SPEC section 5, `test_division_by_zero_blames_caller`). No test pins the behaviour for negative operands. Reason for floor: reason not recorded.
**Resolved in v0.4 (TASK_08)**: floor semantics stay, with a recorded reason (the A/B of ADR-0017 found no gain from removing the operators, so the operators keep their only existing meaning and no program changes); SPEC section 3 "Int division and remainder" pins negative operands and zero divisors; `tests/test_v04_acceptance.py` and `examples/int_division.zehn` pin it. Truncation stays available as `int.div_trunc`.

## Revisit condition
Closed. Reopen only through ADR-0017's revisit condition.
