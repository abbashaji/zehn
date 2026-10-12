# ADR-0002 Non-canonical layout is a warning, an error under `--strict`
Status: unmeasured

## Problem
SPEC invariant 2 says "the parser rejects non-canonical layout". Rejecting every hand-written file that is not already formatted makes the tools awkward to use.

## Options
1. Reject non-canonical layout always (the literal text of invariant 2).
2. Warn by default (`W0301`) and make it an error (`E0203`) only under `--strict` (chosen).

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Option 2. `canonical_diags` in `zehn.py` compares the source with `format_program` output and emits `W0301`, or `E0203` when `strict`. Reason, from CHANGELOG v0.2: "this keeps hand-written files usable". Covered by `test_non_canonical_warns_and_strict_errors`. Known mismatch: SPEC section 0 invariant 2 still says the parser rejects non-canonical layout, while section 11 and section 9 describe the warning/strict split. The invariant text was not changed to match.

## Revisit condition
Proposed here: when SPEC section 0 is next edited, reword invariant 2 to match, or make `--strict` the default once the formatter is the normal way to write files.
