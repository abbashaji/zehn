# ADR-0006 `W0102` (unreachable statement) is a warning, and `--strict` does not promote it
Status: unmeasured

## Problem
After static return-path analysis, a statement that follows a point that always returns can never run. It has to be reported, but it is unclear whether it should stop a program.

## Options
1. Error.
2. Warning, never promoted by `--strict` (chosen).
3. Warning that `--strict` promotes: not recorded as considered.

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Option 2. Reason, from CHANGELOG v0.3: "Dead code is a smell, not a hole." In `zehn.py`, `ReturnChecker` takes no strict flag, so `strict` cannot change it (`strict` only reaches `Checker`, where it adds `E0402`, and the canonical-layout check). `test_unreachable_statement_is_a_warning_not_an_error` pins the warning; no test runs `W0102` under `--strict`, so the "not promoted" half is true in the code but unpinned.

## Revisit condition
Proposed here: if generated programs commonly contain dead code that auditors miss, let `--strict` promote it.
