# ADR-0012 One error-code shape with `E` and `W` prefixes
Status: unmeasured

## Problem
SPEC invariant 6: every error is machine-readable JSON with code, location, cause and fix hint. Warnings and errors need to be told apart by tools, not by prose.

## Options
Not recorded.

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
A code is `E` or `W` plus four digits; the hundreds digit groups the phase (SPEC section 9: `E01xx` lexing, `E02xx` parsing, `E03xx` names and types, `E04xx` examples, `E05xx` runtime contracts, `E06xx` effects, `E07xx` patching, `E08xx` resource limits). Diagnostics are JSON objects with `code`, `severity`, `phase`, `message` and, where relevant, `blame`, `location`, `values`, `fix_hint`. `zehn explain <code>` prints a long text from the `EXPLAIN` table in `zehn.py`. Why this shape: reason not recorded beyond invariant 6.
Gap found while writing this ADR: `E0001` (bad command-line option value, phase `usage`) is emitted by `zehn.py` but has no `EXPLAIN` entry, so `zehn explain E0001` prints "unknown code". Every other emitted code has one. Not fixed here (documentation-only task).

## Revisit condition
Proposed here: add the `E0001` explain text in the next code task; revisit the numbering if a phase outgrows its hundred codes.
