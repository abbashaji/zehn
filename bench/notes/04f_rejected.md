# 04f: rejected tasks

Nothing was rejected: all nine edit tasks (edit_007 to edit_015) are expressible in Zehn v0.3 as it is.

## Calibration choices (from bench/BASELINE_v0.3.md, "Calibration for growth")

- The baseline says `edit` is at its ceiling: pass_repair is 1.0 in all six languages for edit_001 to edit_006, and pass@1 is at the ceiling for python_plain, python_strict, rust and rust_strict. It asks for harder tasks (aim: pass_repair about 0.5 to 0.9 for the strongest non-Zehn language). This branch followed that advice: levels are 2 x L1, 3 x L2, 4 x L3 (22% / 33% / 44%) instead of the plan's 30/40/30.
- Difficulty is raised by the number of interacting rules in the description (up to three error messages with a fixed precedence, per-slice rounding, a stable sort plus tie ranks, comparison against a merged finish), not by obscure wording. Four of the nine are feature additions (edit_008, 010, 013, 015); five are bug reports, three of those with two or more symptoms.
- Whether the new tasks are really harder is NOT measured: no model was run. The expectation that they sit below the ceiling for rust_strict is a guess.
- Starts for feature tasks were written so that the visible examples pass on the start (the python adapters run visible examples in tool_check); hidden tests fail on every start.

## Friction seen while writing them (not rejections; input for the Phase 2 stdlib decisions)

- No list sort, insert, slice or remove: `edit_010` removes the minimum k times by index recursion; `edit_014` needs a hand-written stable insertion sort (`insert_sorted` with a `placed` flag, 20 lines) for something Python, TypeScript and Rust do in one call.
- No Text-to-Int parse and no substring or character access: the only text task that fits is substring search plus upper-casing (`edit_011`); tasks about parsing numbers out of text could not be written.
- Every filter or search that depends on a parameter (tags, ids, brackets) is an index-recursion helper with an accumulator; `Option` sentinels do not exist for "no open item yet", so `edit_015` carries `has_open: Bool` next to two Ints (`open_begin`, `open_finish`), and `edit_009` uses `count == 0` as the "no open run" flag.
- Three sentinel values in recursion helpers (`prev_points = -1` in `edit_014`) rely on the inputs being non-negative.
- Two consecutive `type` declarations need a blank line between them; `zehn fmt` fixes it, but a first draft fails `--strict` with E0203.
- A parameter named `id` is fine in Zehn but shadows a builtin in Python (ruff and mypy do not complain); `end` is still a keyword, so `begin` / `finish` is used again (`edit_015`).
- Rust strict: rustfmt wants `Ranked { name: e.name, rank }` on one line when it fits (a first draft was rejected); TypeScript strict has `noUncheckedIndexedAccess`, so `runs[runs.length - 1]` is `T | undefined` and needs a guard (`edit_009`, `edit_015`).
