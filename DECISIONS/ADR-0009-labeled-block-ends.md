# ADR-0009 Labeled block ends (`end fn`, `end if`, `end match`)
Status: unmeasured

## Problem
How a block closes. SPEC invariant 4: "Every block closes with `end <kind>`."

## Options
Not recorded. The repository does not say which other block endings were considered.

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Every `fn` closes with `end fn`, every `if` with `end if`, every `match` with `end match` (SPEC section 2 grammar). In `zehn.py` the parser eats the `end` keyword and then the kind keyword, so a wrong or missing label is a parse error. Why: reason not recorded beyond the invariant's own wording.

## Revisit condition
Proposed here: if measured model or auditor error rates in Phase 0 show the labels do not reduce structural mistakes, reconsider; any change breaks every existing program, so it needs a version bump.
