# ADR-0001 Pipeline `|>` desugars to nested calls in canonical form
Status: unmeasured

## Problem
`a |> f(b)` is convenient to write, but SPEC invariant 2 says every program has exactly one canonical text. The formatter has to choose one printed form for a pipeline.

## Options
1. Desugar at parse time: `a |> f(b)` becomes `f(a, b)`, and the formatter prints nested calls only (chosen).
2. Keep pipelines in the tree and print a call chain as a pipeline. CHANGELOG v0.2 calls this "possible but a bigger design choice".

## Experiment run (or why none)
None. No experiment is documented in the repository.

## Numeric result
None.

## Decision
Option 1. `Parser.expr` / `insert_first` in `zehn.py` rewrite the pipeline while parsing, so no later stage sees `|>`. SPEC section 2 and section 11 state it ("Pipelines do not survive formatting"). A visible consequence recorded in CHANGELOG v0.2: `examples/transfer.zehn` was rewritten by `zehn fmt`. Covered by `test_pipe_is_desugared`. Why option 1 over option 2: reason not recorded.

## Revisit condition
Proposed here (not recorded earlier): if long pipelines turn out hard for human auditors to read as nested calls, reopen option 2 together with a canonical rule for when to print a chain.
