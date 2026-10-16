# Task 04d (domain, domain_007 to domain_017): rejected tasks

Nothing was rejected: all eleven tasks are expressible in Zehn v0.3 as it is (11 of 11 kept).

Levels: 2 x L1 (007, 008), 4 x L2 (009 to 012), 5 x L3 (013 to 017). That is 18% / 36% / 45% instead of the nominal 30 / 40 / 30: `bench/BASELINE_v0.3.md` ("Calibration for growth") puts domain at the ceiling for python_plain, python_strict, rust and rust_strict (pass@1 above 0.95) and asks for harder tasks, so the split was shifted toward level 3. No domain task is at a floor except domain_003 and domain_005 for zehn only. The difficulty of the new tasks is designed (ordered checks, state threading, rounding at every step, tie rules), not measured: no model has run on them yet.

Friction seen while writing the Zehn references (input for the Phase 2 stdlib decisions, not a rejection):

- `Text` has no ordering: `<` on Text is `E0306` ("expected Int, found Text"). A league table that breaks ties by team name (the natural rule) could not be written, so domain_017 breaks ties by first appearance. Any sort by a text key needs a Text comparison in the stdlib.
- No loops and no list search or update, again: domain_017 needs ten functions (`invalid_from`, `has_team`, `bump`, `record`, `tally`, `better`, `rows_from`, `insert_row`, `sort_rows`, `standings`), most of them index-recursion helpers; domain_012 and domain_014 carry three each. There is no `list.sort`, `list.find`, `list.update` or slice (`rows_from` is a hand-written tail).
- Counting over a list needs a recursive helper (domain_012 `votes_for`), because `list.filter` takes only a named top-level function with one argument and cannot close over the name to count.
- Error messages with several parts still need nested two-argument `text.concat` (up to three levels in domain_007, domain_012 and domain_015); a join or variadic concat would remove them.
- Recursion depth is the only repeat mechanism: domain_015 recurses once per month (36 months at most in the tests, far below the 10000 default depth). A hidden-set task with a long simulation would hit `E0802` in Zehn but not in the other languages.
- No tuple expressions, so helpers that would return two values in the other languages (`rate` triples in domain_007) are split into one function per value (`base_fee`, `extra_fee`, `weight_limit`).

Friction seen in the comparison languages:

- ts_strict has `noUncheckedIndexedAccess`: `candidates[0]` and `votes[i]` are `T | undefined` (TS2532), so domain_012 destructures (`const [first, ...others] = tally`) and domain_016 guards the price lookup with `hasOwnProperty`.
- rust_strict (clippy) refuses an if / else-if chain over a three-way comparison (`clippy::comparison_chain`); domain_017 uses `match scored.cmp(&conceded)`.

Verification notes:

- Expected values in `tests.json` were produced by running `ref.py` (the Python references, typed and checked with mypy strict and ruff by `python_strict`) and then confirmed by the other five adapters; the descriptions were checked against a hand computation for the tricky rows (domain_009 blocks, domain_013 greedy walk, domain_015 first loan, domain_016 prorations, domain_017 BIG table).
- No test divides or takes a remainder with a negative operand. Divisions in the references have a positive dividend and divisor (started hours and kilograms, prorations, interest in basis points, change counts); domain_016 returns a negative number but only after subtracting two rounded non-negative quotients.
- Python 3.9 is only syntax-checked (`ast.parse(..., feature_version=(3, 9))` on the 11 `ref.py`; only 3.12 exists here). Toolchains used: mypy and ruff from pip (latest), tsc 6.0.3, rustc/cargo/clippy/rustfmt 1.75.0.
