# TASK 02d: rejected tasks

Nothing was rejected: all six `effect` tasks (effect_001 to effect_006) are expressible in Zehn v0.3 as it is.

Friction seen while writing them (feeds the Phase 2 stdlib decisions; none of it blocked a task):

- Examples must be pure (E0602) but `--strict` requires at least one example per function (E0402), so an effectful function can never exemplify its own behaviour. The Zehn references give such functions examples that call the pure helpers they use; the console output itself is checked only by the hidden tests.
- A `-> Unit` function must end with `return <effectful call>`, so a recursive print loop cannot end in a base case that returns Unit. The references return a count (`Int`) from the loop helpers instead.
- No loops, so every list walk is a recursive helper with an index and `list.get`; there is no `list.enumerate`/`list.fold` with an effectful callback (effects through callbacks were not tried).
- No text padding or formatting helper: every output line is a nested `text.concat` chain.
