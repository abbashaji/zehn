# 04b: rejected tasks

Nothing was rejected: all eleven tasks (pure_007 to pure_017) are expressible in Zehn v0.3 as it is.

## Calibration choice

`bench/BASELINE_v0.3.md` puts pure/python_plain, pure/python_strict, pure/rust and pure/rust_strict at the ceiling and asks for harder tasks (aim: pass_repair about 0.5 to 0.9 for the strongest non-Zehn language). Levels were therefore shifted harder than 30/40/30: 2 at level 1 (18%), 4 at level 2 (36%), 5 at level 3 (45%). The difficulty of the new tasks is designed (error precedence, carried state, fixed boundaries) and not measured: no model has run on them.

## Friction seen while writing them (not rejections; input for the Phase 2 stdlib decisions)

- No list take, drop or slice: `rotate_left` (pure_013) and the stack machine (pure_014) need hand-written index-recursion helpers.
- No `list.last`: tasks that need the last element use `list.get(xs, list.len(xs) - 1)` (pure_017).
- Stdlib `Text` has no character access, so no pure task here works on the characters of a text; `Text` appears only as instruction names and error messages.
- `Map` is used inside pure_015 and pure_016 (not in the signature, which is allowed); Python uses `dict`, TypeScript `Map`, Rust `HashMap` (one `use` line at the top of the Rust reference).
