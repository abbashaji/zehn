# ADR-0007 Big-integer cost is schoolbook (`wa * wb`)
Status: unmeasured

## Problem
`Int` is arbitrary precision, so one multiplication can allocate or compute without limit. The fuel charge for large integers must bound time and memory.

## Options
1. Schoolbook: `* / %` cost `wa * wb` words, `+ -` cost `max(wa, wb)` (chosen). CHANGELOG v0.3: an upper bound on what CPython really does.
2. Linear cost in the operand size. CHANGELOG v0.3: "allowed multi-second runs".

## Experiment run (or why none)
No script or benchmark is in the repository. The multi-second observation for option 2 is stated in CHANGELOG v0.3 without a method.

## Numeric result
As stated in CHANGELOG v0.3 and SPEC section 13 (not reproduced here): with the default fuel, integers top out near 100,000 bits (about 30,000 decimal digits) under repeated squaring; `2000!` (5,736 digits) fits easily. `test_big_integer_growth_is_stopped_quickly` only checks that runaway squaring ends in `E0801` in under 3 s.

## Decision
Option 1. The price, recorded in CHANGELOG v0.3: integers are capped near 100,000 bits at default fuel; larger numbers need a larger `--fuel`. Charged before the operation (`Interp` binary-operator code), and operands up to 128 bits are free.

## Revisit condition
Proposed here: if programs that legitimately need larger integers are common, or a measured cost model (for example Karatsuba-aware) can be shown to bound time as well.
