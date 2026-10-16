Nothing rejected in 04h: all eight edit tasks (edit_025 to edit_032) were expressible in Zehn v0.3 as it is.

Difficulty choice: BASELINE_v0.3.md ("Calibration for growth") says `edit` sits at the ceiling for python_plain, python_strict, rust and rust_strict (every language reaches pass_repair 1.0 on edit_001 to edit_006) and advises harder tasks. The levels are therefore shifted from 30/40/30 to 1 L1, 3 L2, 4 L3 (12.5/37.5/50 percent). Harder here means: two interacting rules or two bugs in one task, a fixed error-check order that must survive the change, and boundary cases in the tests. Whether this lands in the advised pass_repair band of 0.5 to 0.9 for the strongest non-Zehn language is unmeasured. Features: edit_026, edit_029, edit_031 (3 of 8).

Zehn stdlib friction (input for Phase 2, not rejections):
- No list slice, tail or sort: edit_030 pops the queue front by rebuilding the list with an index helper, and edit_032 places each player by counting how many players come before it (O(n^2)).
- No conditional expression: edit_029 and edit_031 use `var` plus `if` to compute a value that Python, TypeScript and Rust write as one expression.
- `implies` binds tighter than `and`, so `a and b implies c` reads as `a and (b implies c)`; contracts need explicit parentheses (edit_025).

Toolchain notes: the TypeScript adapter rejects unchecked indexing (`xs[mid] < target` is TS2532), so ref.ts and start.ts of edit_027 cast with `as number`; clippy 0.1.97 flags `sort_by(|a, b| b.x.cmp(&a.x))` (unnecessary_sort_by), so start.rs of edit_032 uses `sort_by_key` with `std::cmp::Reverse`.
