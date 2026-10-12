# ADR-0004 The fuel cost model
Status: unmeasured

## Problem
Zehn has no loops, so unbounded work comes only from recursion and large data. SPEC invariant 8 requires that a run ends in a diagnostic, never a hang or a host crash, and SPEC section 13 requires that it ends at the same point on every machine.

## Options
Not recorded, except for the big-integer pricing (see ADR-0007).

## Experiment run (or why none)
None documented in the repository. `tests/test_zehn.py` pins behaviour (`test_fuel_is_deterministic`, `test_list_operations_are_charged_by_size`, `test_big_integer_growth_is_stopped_quickly`) but does not compare alternatives.

## Numeric result
None for the model as a whole.

## Decision
Deterministic fuel, specified in SPEC section 13 and implemented in `Interp.tick`:
- Budget is per entry point (one `example`, one `zehn run`, one `Interp.invoke`); `fresh_budget` resets it and budgets are never shared.
- 1 step per expression node and per statement.
- Size-proportional extra charge for the operations in `LINEAR_BUILTINS` (list, text and map operations); `int.to_text` also pays about `w^2 / 4`.
- Integer `+ - * / %` with an operand over 128 bits are charged extra, before the operation runs, so a runaway product is stopped before it allocates.
Why this shape: reason not recorded beyond the SPEC section 13 consequences (memory and wall-clock time are bounded, no machine dependence).
Known mismatch: the code also charges `wa * wb` for the comparisons `< <= > >=` when an operand exceeds 128 bits (the line after the `==`/`!=` early return in the binary-operator code), but the SPEC section 13 table lists only `+ - * / %`. Not changed here (documentation-only task).

## Revisit condition
Proposed here: when SPEC section 13 is next edited, reconcile the comparison charge; or earlier if real programs show a cost that does not track wall-clock time.
