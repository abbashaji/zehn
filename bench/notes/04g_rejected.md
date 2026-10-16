# TASK 04g (edit_016 to edit_024): rejected tasks

Nothing was rejected: all nine edit tasks are expressible in Zehn v0.3 as it is (9 of 9 kept).

## Calibration

`bench/BASELINE_v0.3.md` (section "Calibration for growth") says the `edit` category is at a ceiling: pass_repair 1.0 in all six languages, no task where any language is below 1.0, and pass@1 at or near 1.0 for the non-Zehn languages. Following its advice ("new tasks should be harder"), the levels are 2 x L1, 3 x L2, 4 x L3 instead of the 30/40/30 split (3/4/2 in nine tasks). Four of the nine are feature additions (edit_017, 019, 021, 023); the rule asks for at least three. The difficulty is by design (several interacting rules, error precedence, repeated values, tie and boundary cases); it is not measured: nobody has run a model on these nine tasks.

## Friction seen while writing them (input for the Phase 2 stdlib decisions, not rejections)

- No list search, insert, take or drop: dropping one element (edit_022), merging two sorted lists (edit_024) and a sliding window (edit_019) are all index recursions with accumulators. A merge of two lists needs a four-way `match` over `list.get(a, i)` and `list.get(b, j)`.
- No `list.last` and no negative-safe indexing note in the spec: edit_024 checks `list.len(done) == 0` before `list.get(done, list.len(done) - 1)` so it never relies on how `list.get` treats an index below 0 (the spec only says out-of-range returns `none`).
- No `list.min` / `list.max` / `list.zip`: edit_022 hand-writes `lowest`; edit_018 needs `option.unwrap_or(list.get(...), 0)` to pad the shorter list with zeros.
- `text.to_upper` is the only case helper, so case-insensitive comparison (edit_023) works by upper-casing both sides; no `text.to_lower`, no trim.
- Examples must be pure and at least one per function in strict mode; helpers with several parameters (`compare_from`, `drop_first`, `merge_from`) need hand-picked examples that spell out the accumulator arguments.

## Friction in the comparison languages

- TypeScript strict mode here has `noUncheckedIndexedAccess`: `a[i]` is `number | undefined`, so the TS references use `?? 0` where an index is known to be in range. Python and Rust need nothing.
- Starts that ignore a parameter (edit_017, 019, 021, 023) name it `_year`, `_window`, `_daily_cap`, `_limit` in Rust to stay clean under clippy; Python and TypeScript pass their checks with the parameter unused (the same pattern as edit_006).
- Rust references avoid `Option::is_none_or` (needs rustc 1.82); edit_020 compares `Option<i64>` values directly (`None` sorts below every `Some`).
