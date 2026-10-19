# ADR-0017 Integer division: operators or explicit functions (prepared, not decided)
Status: measured

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
Run on 2026-10-18/19 with the workflow `.github/workflows/experiments.yml` (`bench/experiments/int_division/`): model `gemini:gemma-4-31b-it` (free tier), 50 tasks (30 dev control tasks plus the 20 `numneg` tasks), A = `default`, B = `int_ops=explicit`, `simpler` = `a`. The planned 5 repeats were cut to 3 (150 runs per side); 297 of the 300 runs completed. Three runs (A: `numneg_013` repeat 3 and `effect_001` repeat 1; B: `numneg_018` repeat 2) kept failing with Google server errors (HTTP 500/503) after every retry and are left out; they are 1% of the runs and do not change the picture. Before the valid run the adapter was fixed so that the default arm's prompt no longer documents `int.div_floor`, `int.div_trunc` and `int.rem_euclid` (SPEC.md is the base prompt of every arm; a default-arm model that knew the functions could use them instead of `/` and `%`). The variant file `int_ops=explicit.md` still documents them for B. Before that, the checks of the pack stood as written: the 20 Zehn refs and 20 Python refs pass their hidden tests, and swapping the rounding function in a Zehn ref makes the tests fail for every task except `numneg_018` (equivalent mutant: its division is exact).

## Numeric result
Paired over the 50 tasks, difference = A - B, 95% CI from 10,000 resamples (`report.py ab`, computed on the 297 completed runs):

| metric | A (operators) | B (explicit) | A - B | 95% CI |
|---|---|---|---|---|
| pass@1 | 0.707 | 0.713 | -0.007 | [-0.093, 0.073] |
| pass_repair | 0.947 | 0.947 | 0.000 | [-0.053, 0.047] |
| repair rounds | 0.660 | 0.987 | -0.327 | [-0.520, -0.127] |
| silent-bug rate | 0.027 | 0.007 | +0.020 | [-0.013, 0.067] |
| total tokens | 18,178 | 23,387 | -5,209 | [-7,372, -3,075] |

`report.py` says `DECISION: keep a` (the pass_repair CI includes 0). On the 20 `numneg` tasks both sides solve 91.5% on the first try and 100% after repair, so the rounding stated in the description is followed either way and there is no room for B to gain. In 41 of B's 149 runs (32 in the first attempt) the model wrote `/` or `%` and got `E0312`, which costs about 0.33 extra repair rounds per run and about 29% more tokens. Limits: one model, 3 repeats, so the CIs are wide; 6 of the 30 control tasks have refs that use `/` or `%`, so B is penalised there by design (see RUN.md); whether a model picks the right function name is a separate effect from whether it knows the semantics, and the A/B cannot separate them.

## Decision
Default unchanged: option 1 behaviour, flag `int_ops=operators`. The three functions are added permanently (they are additive and cost the same fuel as the operators). By the rule above the operators stay, since the CI of the pass_repair difference includes 0 and B costs repair rounds and tokens; the formal choice between options 1 and 2 is still taken in TASK_08.

## Revisit condition
After the A/B of TASK_08. Also revisit if a non-negative integer type is ever added (option 3) or if a model
run shows `int.rem_euclid` being used where a floor remainder was meant.
