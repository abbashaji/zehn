# ADR-0011 No lambdas: stdlib takes named top-level functions only
Status: unmeasured

## Problem
Higher-order stdlib functions (`list.map`, `list.filter`, `list.fold`, `option.map`, `result.map`, `result.map_err`) need a way to receive a function.

## Options
Not recorded. The grammar has no lambda syntax and no function-typed parameters.

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Only named top-level functions can be passed (SPEC section 3: function types `Fn(A) -> B` "only exist for named top-level fns (no lambdas, no function-typed parameters)"; SPEC section 8: "no lambdas"). Naming a function as a value needs its effects to be a subset of the caller's `uses` (`E0601`, SPEC section 6, added in v0.2). Why: reason not recorded; it is consistent with SPEC invariant 3 ("nothing implicit") but the files do not say that this was the reason.

## Revisit condition
Proposed here: if Phase 0 programs need many one-use helper functions only to call `list.map` or `list.fold`, reconsider (it would also need effect and type rules for anonymous functions).
