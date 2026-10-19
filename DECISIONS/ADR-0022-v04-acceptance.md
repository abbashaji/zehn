# ADR-0022 v0.4 acceptance: Phase 1 closed
Status: decided (all four roadmap section 5 criteria met; two decisions underpowered, see below)

(TASK_08 named this file ADR-0020-v04-acceptance.md; ADR-0020 is the recursion ADR and ADR-0021 is tuples, so it is numbered 0022.)

## Problem
Close Phase 1: settle the two open decisions with the experiment numbers, check every acceptance criterion of roadmap section 5, bump the language to v0.4.

## Options
Per decision the roadmap A/B rule applies (variant wins only if the pass_repair CI excludes 0, else the status quo stays). Nothing else was open.

## Experiment run (or why none)
Both A/B runs were made with `.github/workflows/experiments.yml` on `gemini:gemma-4-31b-it`, 3 repeats instead of 5; the results are in `bench/results/{effect_examples,int_division}-gemini-gemma-4-31b-it-{a,b}` and `bench/results/{effect_examples,int_division}-ab.md` (`python3 bench/report.py ab --a <a run> --b <b run> --simpler a`). Both are **underpowered** (3 repeats; effect_examples also 17 tasks, not 50). Both reports say `DECISION: keep a`.

| decision | pass_repair A - B | 95% CI | outcome |
|---|---|---|---|
| int_ops=explicit (ADR-0017) | 0.000 | [-0.053, 0.047] | operators stay; floor semantics specified in SPEC |
| effect_examples=mock (ADR-0019) | -0.034 | [-0.111, 0.041] | default `off`; strict rule option B implemented |

## Numeric result
Acceptance criteria of roadmap section 5, each with the command run on the final tree:

| # | criterion | evidence | met |
|---|---|---|---|
| 1 | baseline benchmark published | `ls bench/BASELINE_v0.3.md` lists the file; it is the report of `bench/results/baseline-gemini-gemma-4-31b-it` (900 records, 0 errored). The Phase 0 gate itself (ADR-0016) is still `proposed`: the builder has not decided it. | yes (publication); gate decision pending |
| 2 | recursion analysis has zero false positives on all examples | `for f in examples/*.zehn; do python3 zehn.py check $f --strict --json \| grep -c E0311; done` prints 0 for all 7 files; `tests/test_recursion.py` (42 tests, includes a 400-program soundness check) green | yes |
| 3 | SPEC contains no unspecified behaviour in known limitations | `grep -n -i "unspecified\|not yet\|undefined" SPEC.md` prints two lines: line 13 (invariant 7, "No undefined behavior": a promise, not a gap) and line 159 (division by zero "never undefined behavior": the defined diagnostic E0505). Section 12 holds no such word. The old items were closed: division semantics (section 3), tuples (grammar, section 3), recursion bullet (section 12). | yes |
| 4 | at least 150 tests | `python3 -m unittest discover -s tests` reports `Ran 337 tests ... OK` (final count in the summary of the run) | yes |

Other "done when" items: `sh ci/run_ci.sh` exit 0 (see the final run below); `python3 zehn.py check <f> --strict` for every `examples/*.zehn` prints `OK: 0 error(s)` (effects 1 example, int_division 9, inventory 11, recursion 9, shapes 8, transfer 5, tuples 29); ADR-0017, ADR-0019 and ADR-0010 carry numbers and `Status: decided`.

Not met / open: the ADR-0016 gate decision (stop Phase 1 or continue) is the builder's and is still `proposed`; TASK_08 text refers to it as ADR-0014 and to the effect ADR as ADR-0015, which are ADR-0016 and ADR-0019 in this repository.

## Decision
Phase 1 is closed at v0.4. Division keeps `operators` with floor semantics; `effect_examples` keeps `off`, and `--strict` demands an example only of pure functions. Both are pinned by `tests/test_v04_acceptance.py`.

## Revisit condition
Phase 2 planning starts from ADR-0016 (the builder's gate decision). Re-run the two A/Bs with 5 repeats and a second model before treating either result as more than "no evidence of a gain".
