# ADR-0020 Unconditional recursion is a static error (`E0311`), found per cycle with a conservative definition
Status: measured

## Problem
`fn f(n) = f(n)` and mutual versions of it can never return, yet they reached run time and ended in `E0801` or `E0802` after thousands of wasted steps (and, for `run`, after any effects of earlier statements). The check must catch them before any example runs and must never reject a function that can return, because a false positive blocks a correct program, while a miss only costs a run-time limit.

## Options
1. Error vs warning. (a) Error `E0311` (chosen). (b) Warning: the program would still run its endless example and fail at run time anyway, so the warning adds noise without saving anything.
2. Scope. (a) Whole program: find cycles of the call graph across all functions (chosen). (b) Per function: only self calls; misses `ping`/`pong`, which `errors/bad_termination.zehn` contains.
3. Strictness of "certain call". (a) Conservative (chosen): count a call only in straight-line code, in arguments and operands of those calls, and in `if` conditions / `match` subjects, before any `return` or `?`; an `if` or `match` that contains `return` or `?` ends the certain part. (b) Count calls in every branch of an `if` / every case of a `match` ("all branches recurse"): finds more, but needs path reasoning that must be proved sound; not recorded as needed by any current program. (c) Count every call: flags `fib`.

## Experiment run (or why none)
The chosen definition was run on every Zehn program the repository holds, and on a generated soundness corpus (`tests/test_recursion.py`: 400 programs, fixed seed 20260311, 1 to 3 functions, 16 body shapes: direct calls, calls in arguments, in conditions, under `if` / `match` / `and` / `or`, after `?`, after `return`, as a value). Every flagged program was run from each function of its cycle with fuel 2000 and depth 40 on inputs -1, 0, 2: all ended in `E0801` or `E0802`. Mutating the pass to count the right side of `and` / `or`, or to forget a `?` inside a short-circuit operand, makes the tests fail.

## Numeric result
- False positives on the 100 reference programs (`bench/run.py verify-refs --lang zehn`): 0 (100 of 100 OK).
- False positives on all 138 Zehn files under `bench/tasks` and `examples/` (133 + 5): 0 `E0311`.
- Soundness corpus: 400 programs, 145 flagged, 0 flagged programs returned.
- `errors/bad_termination.zehn`: 2 diagnostics (the `spin` self loop, the `ping` -> `pong` cycle); `fib` is not reported.
Options 1(b), 2(b), 3(b) and 3(c) were not measured; only the chosen definition was.

## Decision
Options 1(a), 2(a), 3(a). One diagnostic per elementary cycle (so two cycles through one function give two diagnostics); at most 200 cycles per program are listed, a safety valve for pathological graphs that no repository program comes near. The definition ignores run-time errors that could end a run before the call (division by zero, a failing `requires`, `unwrap` of `err`): such a function can never *return*, which is what the code claims. This ADR was written as ADR-0016, a number `ADR-0016-phase0-gate.md` already uses; the merge (TASK_06m) renumbered it to 0020.

## Revisit condition
Proposed here: if generated programs commonly contain recursion whose every branch recurses, or run-time `E0801` / `E0802` on conditionally guarded recursion dominates the failures of a benchmark run, add option 3(b) with a soundness proof.
