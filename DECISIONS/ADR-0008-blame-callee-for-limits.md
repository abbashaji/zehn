# ADR-0008 Blame for `E0801` and `E0802` is `callee`
Status: unmeasured

## Problem
Every runtime diagnostic names who is to blame (SPEC section 9). For fuel and call-depth exhaustion, it could be the function that ran out, the caller that passed a big input, or the host that set the limit.

## Options
1. `callee` (chosen).
2. `caller` or `host`: not recorded as considered. For comparison, `E0604` (capability not granted) is blamed on the host (SPEC section 6).

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Option 1. Reason, from CHANGELOG v0.3: "the usual cause is a missing base case". If a legitimately large input hits the limit, "the fix is on the host side (`--fuel`)". In `zehn.py`, `Interp.limit_error` and `host_stack_error` both set `blame="callee"`; SPEC section 13 says both diagnostics blame `callee`. A test asserts it for `E0802` (`blame == "callee"` in the call-depth tests).

## Revisit condition
Proposed here: if the diagnostics are mostly caused by legitimate large inputs, blame the host (limit too low) or the caller instead, or add a distinguishing field.
