# ADR-0013 Excluded features: no operator overloading, macros or subtyping (traits and inheritance: see Decision)
Status: unmeasured

## Problem
Which common language features Zehn leaves out on purpose. The task for this ADR also names traits, overloading and inheritance and cites roadmap section 6; the roadmap is not in this repository, so only what SPEC.md says is verified here.

## Options
Not recorded.

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Supported by SPEC.md:
- No operator overloading and no macros (SPEC section 0, invariant 3, "Nothing implicit").
- No subtyping and no implicit conversion (SPEC section 3).
- No aliases: "If two names could mean the same thing, only one exists" (SPEC section 8).
- Two top-level definitions with the same name are an error, `E0202` (`zehn.py` `EXPLAIN`), so functions are not overloaded in practice.
Not supported by the files: SPEC.md does not mention traits or inheritance, and does not list function overloading as an exclusion. They are excluded only in the sense that the grammar has no syntax for them. The reasons for all of these beyond invariant 3: reason not recorded. Roadmap section 6 is the cited source for the full list and should be checked when this ADR is revised.

## Revisit condition
Proposed here: revisit a feature only if Phase 0 shows programs cannot be written without it; adding any of them is a breaking change (ADR plus version bump).
