# ADR-0010 `/` and `%` on `Int` use floor semantics (OPEN: must be resolved in v0.4)
Status: unmeasured

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
**Must be resolved in v0.4**: choose one rule, write it into SPEC, pin it with tests, and update this ADR. Changing it is a breaking change (ADR plus version bump).

## Revisit condition
v0.4, unconditionally.
