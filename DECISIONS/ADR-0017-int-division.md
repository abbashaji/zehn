# ADR-0017 Integer division: operators or explicit functions (prepared, not decided)
Status: unmeasured

## Problem
ADR-0010 left the rounding of `/` and `%` on Int open: the code is Python's floor division, which is not a
deliberate choice, and a model that expects truncation (C, Rust, TypeScript, Java) gets `-7 / 2 == -4`
instead of -3, silently. SPEC invariant 7 wants determinism and no hidden behaviour. This ADR prepares the
choice (roadmap section 5, item 3); TASK_08 takes it.

## Options
1. **Keep the operators** (`/` and `%` with floor semantics, the v0.3 default). Shortest to write; the rounding
   is invisible at the call site and differs from most languages a model has seen.
2. **Remove the operators for Int** (dialect `int_ops=explicit`): division is written `int.div_floor`,
   `int.div_trunc` or `int.rem_euclid`, so the rounding is always in the name. Costs: longer code, an
   extra repair round when a model writes `/` out of habit (`E0312`), and no explicit name for the floor
   remainder (the roadmap lists these three): `int.rem_euclid` equals the floor remainder only for a
   positive divisor, so a remainder that follows the divisor's or dividend's sign is written `a - b * q`.
3. **Remove them only for negative-capable types.** Zehn has a single integer type (Int, which can be
   negative), so this option has no meaning today; it needs a non-negative type first (no such type is planned
   in the repository). Listed because the roadmap lists it, not evaluated.

## Experiment run (or why none)
None yet. The pack is ready in `bench/experiments/int_division/` (`experiment.json`, `RUN.md`, 20 `numneg`
tasks, prompt addendum `bench/variants/int_ops=explicit.md`). Only the reference solutions were checked:
the 20 Zehn refs (in the explicit form, valid in both dialects) and 20 Python refs pass their hidden tests,
and swapping the rounding function in a Zehn ref makes the tests fail for every task except `numneg_018`
(equivalent mutant: its division is exact). No model has run. Planned: A = default, B = `int_ops=explicit`,
50 tasks x 5 repeats, one model per run pair.

## Numeric result
None.

## Decision
Default unchanged until the experiment is run: option 1 behaviour, flag `int_ops=operators`. The three
functions are added permanently (they are additive and cost the same fuel as the operators). The choice
between options 1 and 2 is taken in TASK_08 from `report.py ab`; `simpler` is `a` (keep the operators), so
the operators stay unless the CI of the pass_repair difference excludes 0 in favour of B.

## Revisit condition
After the A/B of TASK_08. Also revisit if a non-negative integer type is ever added (option 3) or if a model
run shows `int.rem_euclid` being used where a floor remainder was meant.
