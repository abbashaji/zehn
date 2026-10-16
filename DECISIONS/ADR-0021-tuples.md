# ADR-0021 Tuples: positional values, taken apart only by `match`
Status: unmeasured

## Problem
The v0.3 type checker had a `Tuple` type constructor, but the language could neither build nor take apart a tuple, so a function that returns two values needed a one-off record type (`type MinMax = { lo: Int, hi: Int }`) and every caller paid for it in declarations. Roadmap section 5, item 4. The risk of adding tuples is a second way to do everything: positional access next to patterns, `let` destructuring next to `match`, `(x)` next to `(x,)`. SPEC invariant 2 (one canonical form) argues for exactly one way to build and one to take apart.

## Options
1. **Build with `(a, b)`, take apart with `match` only** (chosen, binding decision of the plan). Two or more elements; no one-element or empty tuple; no `p.0`; no `let (a, b) = p`.
2. Add positional access `p.0` / `p.1`. Shorter for pairs, but a second way, and it hides the meaning of the parts exactly where a record would name them.
3. Add destructuring `let (a, b) = p`. Familiar to a model that knows Python, Rust or TypeScript, but it is irrefutable-only syntax next to a refutable `match` pattern with the same shape: two ways.
4. No tuples; records only. Nothing new to learn, at the price of a type declaration per returned pair.

## Experiment run (or why none)
None. No API key in the build sandbox, and the benchmark has no task that needs a pair yet. Whether a model reaches for `p.0` or `let (a, b)` and what the dedicated errors cost it is exactly what the dedicated errors would let a later run measure.

## Numeric result
None. Facts measured while building: `tests/test_tuples.py` (70 tests) pins the behaviour; the 60 golden files that existed before are byte-identical; a tuple literal costs the same fuel as a list literal of the same elements.

## Decision
Option 1. The two forms people will try from other languages are rejected with their own error and a fix hint that shows the `match` form, instead of a bare `E0201`, because a model that reads one diagnostic and fixes it is the case the language is built for: `E0316` (`let (a, b) = ...`), `E0317` (`p.0`).

Choices made while building, all revisable:
- **Error codes.** `E0313` pattern size, `E0314` tuple size at any place where two tuple types meet (one rule: if both sides are tuples and the sizes differ, it is `E0314`, never `E0306`), `E0315` tuple pattern on a non-tuple, `E0318` empty or one-element tuple. A wrong element in a tuple of the right size stays `E0306` and is reported on the element. `E0319` is unused.
- **`(T)` as a type is now `E0318`.** Before this task it parsed as a one-element `Tuple`, which no expression could build. This is the only change for a program that was accepted before (a function taking such a parameter and never called with a value of it); the golden files do not contain one.
- **Type text.** Messages and `expected` / `found` write `(Int, Text)`, not `Tuple<Int, Text>`; done in `typecheck.py` because `types.py` was outside this task. A diagnostic that used to print `Tuple<...>` (only reachable through a declared tuple type) changes.
- **Exhaustiveness** is a matrix check over the whole pattern tree, used only when a `match` has a tuple pattern at the top; matches without one run through the v0.3 code unchanged. When the patterns of a match disagree among themselves (different sizes, mixed families) it reports nothing and leaves the report to the type checker, so one mistake gives one code.
- **Runtime value** is its own class `Tup`, not a Python tuple (those are used inside `V` and `MapV`) and not a list (`==` between them is false and a type error statically).
- **`run` JSON** is type-directed: a JSON list is a tuple only where the declared type is a tuple. A global rule (every JSON list that looks like a pair) would break `List<Int>` arguments. Results are printed with `show`, unchanged.
- **Known gap.** The recursion pass (`E0311`) treats a tuple as an expression it does not know and counts nothing after it, so it stays free of false positives but misses recursion hidden in a tuple element. That file was outside this task.
- The ADR number is 0021, not the 0019 reserved in the plan: the merge of v010 renumbered the earlier ADRs and 0019 and 0020 are taken.

## Revisit condition
When a benchmark run shows models writing `p.0` or `let (a, b) = p` and still failing after the hint, or when the dedicated errors are never seen in a run of 100 tasks and the code is dead weight; then reconsider option 2 or 3. Reconsider the one-element tuple only if generic code (a future `Pair<A, B>`) needs it.
