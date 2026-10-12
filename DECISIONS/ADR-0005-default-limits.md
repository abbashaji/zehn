# ADR-0005 Defaults: fuel 1,000,000 and call depth 10,000
Status: unmeasured

## Problem
The two budgets from ADR-0004 need default values that stop runaway programs quickly but still let ordinary recursive code finish.

## Options
Recorded in CHANGELOG v0.3: keep depth 10,000 (chosen), or lower the depth "if you would rather make deep non-tail recursion impossible". Other fuel values: not recorded.

## Experiment run (or why none)
No script or benchmark is in the repository. CHANGELOG v0.3 reports an observation, not a method.

## Numeric result
As reported in CHANGELOG v0.3 (not reproduced here as a measurement): at these values `fib(40)` by double recursion is `E0801` after about 1 s, while `sum_to(5000)` by plain recursion passes. A spot check while writing this ADR (no timing taken): `fib(40)` with the defaults gives `E0801` after 1,000,000 steps at call depth 34, and `examples/recursion.zehn` `sum_to(5000)` returns 12502500.

## Decision
`DEFAULT_FUEL = 1_000_000` and `DEFAULT_DEPTH = 10_000` in `zehn.py` (SPEC section 13). `test_default_depth_is_10000` pins the depth; no test pins the default fuel value. Why these two numbers beyond the fib/sum_to observation: reason not recorded.

## Revisit condition
CHANGELOG v0.3 lists this under "Decisions worth a second look". Reopen when the Phase 0 benchmark programs show typical legitimate programs hitting either limit, or if deep non-tail recursion should become impossible.
