# ADR-0003 `console` and `time` are reserved namespaces
Status: unmeasured

## Problem
Runtime capability enforcement (`E0603`, `E0604`) can only be real if the standard library has at least one effectful function to enforce it on.

## Options
1. Add effectful stdlib functions `console.print` and `time.now`, which makes `console` and `time` reserved namespaces like `list`, `text` and the others (chosen).
2. Leave enforcement untested until a later stdlib growth: not recorded as considered.

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Option 1. Reason, from CHANGELOG v0.2: "capability enforcement needs at least one effectful stdlib function to be real". In `zehn.py`, `NAMESPACES` is derived from the keys of `BUILTINS`, and `RESERVED` adds `ok err some none out`; binding a reserved name is `E0307`. SPEC section 1 lists the reserved namespaces `list text int option result map console time`. Effects of the two functions: SPEC section 6.

## Revisit condition
Proposed here: when a new effectful stdlib namespace is added (the `fs`, `net`, `db`, `rand`, `clock` effects have no functions yet), check that reserving its name does not break existing programs, and write a new ADR.
