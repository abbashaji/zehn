# 04e: rejected tasks

Nothing was rejected: all eleven effect tasks (effect_007 to effect_017) are expressible in Zehn v0.3 as it is.

## Level mix and calibration

`BASELINE_v0.3.md` (Calibration for growth) says `effect` is the only category with headroom for the strongest
non-Zehn languages and asks for harder tasks (pass_repair between about 0.5 and 0.9 for the strongest non-Zehn
language). The plan's 30/40/30 split would be 3/4/4 of 11; this branch uses 2/4/5 (L1: 007, 008; L2: 009 to 012;
L3: 013 to 017). The L3 tasks lean on what the baseline showed to be hard in effect tasks: state carried across
steps, early exit with output already printed, `Result` returns, insertion-ordered storage, a stable sort, and
two-pass layout (measure, then print). These are proposals, not measurements: no model was run on the new tasks.

## Friction seen while writing them (not rejections; input for the Phase 2 stdlib decisions)

- No text slice, char access or padding helper: `effect_013` writes `repeat_text`, `pad_right`, `pad_left` by
  recursion on `text.concat`. No list join either: `effect_016` writes `show_from` for `1,2,3`.
- No list tail, take or drop: removing the top of a stack (`effect_016`) rebuilds the list by index recursion
  (`take_from`), and sorted insertion (`effect_017`) needs a `tail_from` copy. A stable insertion sort over
  `map.keys` takes five helper functions.
- Examples cannot name the parameters of the function they belong to, and effectful functions cannot be called in
  examples (E0602), so every effectful function carries examples on its pure helpers; the first drafts of
  `effect_010` and `effect_011` hit E0302 by writing parameter names in examples.
- A function that prints needs a value to return: `effect_010` (`print_range`), `effect_014` (`print_entries`) and
  `effect_017` (`print_ranked`) return an index, the unchanged store or a count so the printed work has a result
  that the caller uses. There is no way to write a `-> Unit` loop that ends without an effectful call.
- `if` without `else` is allowed as a statement (used in `effect_011` for the wait line), but every other branching
  has to return on both sides, so a conditional print followed by a shared return needs the `if` form without `else`.
- `Int` `/` is floor division in Zehn: `effect_010` and `effect_015` divide only non-negative numbers by positive
  ones, as the comparability constraints require.

## Tool findings while verifying

- `rust_strict` rejects `if mine > theirs ... else if mine == theirs ...` (clippy `comparison_chain`, rustc 1.75
  clippy): the reference uses `cmp` and a `match`. Newer clippy may flag other patterns in the new Rust references.
- rustfmt reflows long method chains and `if` expressions inside call arguments: all `ref.rs` files were run through
  `rustfmt --edition 2021`.
- Verified with: mypy 2.4.0, ruff 0.17.0, tsc 6.0.3, rustc and clippy 1.75.0 (apt). Python 3.9 is checked only with
  `ast.parse(..., feature_version=(3, 9))` on the new `ref.py` files; the sandbox has Python 3.12 only.
- `effect_015`: `Math.floor(t / window)` was checked to equal exact integer division on every test input, so a
  plain TypeScript solution is not penalised by float rounding.

## Not done

- `effect_004` and `effect_006` (flagged in the baseline as possible task defects) were not changed or reviewed;
  they are outside this branch's allowed paths.
