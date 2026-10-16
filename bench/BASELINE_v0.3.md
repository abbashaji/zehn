# Phase 0 baseline: Zehn v0.3 on gemini:gemma-4-31b-it

Baseline label: `zehn.py` sha256 `0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73` (from `meta.json`); identical to the current `zehn.py`.

## Summary

Every hypothesis verdict below is `(underpowered)`: 30 tasks, 5 repeats, one model, one temperature. Nothing in this file is a refutation in the sense of roadmap section 14, and the file does not call anything refuted. The gate rule (roadmap section 3.6) is applied anyway: the H5 point estimate (pass_repair, zehn - rust_strict) is -0.013 with a 95% CI of [-0.040, 0.013], which is worse than rust_strict, so the rule's output is **"stop Phase 1, apply section 14"**. The interval contains 0 and the gap is 7 failed runs of 150 for zehn against 5 of 150 for rust_strict; the builder takes the decision. No top-up is needed: 0 of 900 records carry an error (largest per-language share 0.0%, limit 3%).

Key numbers (all from the tables below):

- First try: pass@1 zehn 0.573 against python_plain 0.947 and rust_strict 0.967. After the tool loop: pass_repair zehn 0.953, python_plain 0.947, rust_strict 0.967.
- Cost: total tokens per run zehn 21699.7 against python_strict 3096.8; repair rounds zehn 0.947 against python_strict 0.013.
- Zehn's round-1 input is about 5485 tokens larger than python_plain's (provider-reported, see Threats), and `SPEC.md` is resent on every round.
- Gate: H5 point estimate worse than rust_strict (the rule fires).

## Method

- Model `gemini:gemma-4-31b-it`, temperature 1.0, up to 5 rounds per run, 5 repeats, seed 1234, set `dev`; runner tools: mypy 2.4.0 (compiled: yes), ruff 0.17.0. 9 sessions on the workflow runner (first 2026-10-12T20:42:59Z, last 2026-10-14T21:14:23Z).
- 30 tasks x 6 languages x 5 repeats = 900 runs expected, 900 records in `records.jsonl`.
- Report command (only the baseline folder; the pilot folders `pilot-gemini-gemma-4-31b-it` and `pilot-gemini-gemma-4-31b` are smoke tests and are not pooled):

  `python3 bench/report.py --run bench/results/baseline-gemini-gemma-4-31b-it --exclude-errors --out bench/BASELINE_v0.3.md`

- Metrics are those of `bench/benchlib/metrics.py`: pass@1 = first_try_pass; pass_repair = a candidate was accepted by the tool and passes the hidden tests; repeats are averaged inside a task, the bootstrap resamples tasks (10000 resamples, seed 1234, 95% percentile interval).
- Figures in the quota tables under Calibration are proposals (plan constants and one reallocation), not measurements; every other number is computed from `report.py` output or from `records.jsonl` / `meta.json`.
- Runs with a non-null `error` are dropped before any metric (`--exclude-errors`; `report.py` has left them out since v006, the flag also prints the table below even when it is empty). Raw files are untouched.

| lang | valid runs | dropped | error message (first 80 chars) |
|---|---|---|---|
| python_plain | 150 | 0 | - |
| python_strict | 150 | 0 | - |
| rust | 150 | 0 | - |
| rust_strict | 150 | 0 | - |
| ts_strict | 150 | 0 | - |
| zehn | 150 | 0 | - |

History: earlier snapshots of this run contained records with `error` set, all of the form "ModelError: giving up after 6 attempts (HTTP 500 ...)" (a few HTTP 503), i.e. Google returned "Internal error encountered" and the client gave up. These were provider failures, not language failures. `--resume` moved them to `records.errors.jsonl` (601 records, kept in the results folder) and redid them in later sessions; none remain in `records.jsonl`.

## Metrics table

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 150 | 0.947 | 0.947 | 0.000 (censored 0/150) | 0.053 | n/a | 2492.3 | 0.008 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 150 | 0.953 | 0.953 | 0.013 (censored 0/150) | 0.047 | 0.000 | 3096.8 | 0.013 |
| rust | default | gemini:gemma-4-31b-it | 30 | 150 | 0.953 | 0.960 | 0.007 (censored 0/150) | 0.040 | 0.000 | 2251.8 | 0.011 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 150 | 0.967 | 0.967 | 0.100 (censored 0/150) | 0.033 | 0.000 | 3025.1 | 0.016 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 150 | 0.580 | 0.947 | 0.380 (censored 0/150) | 0.053 | 0.421 | 4300.4 | 0.144 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 150 | 0.573 | 0.953 | 0.947 (censored 3/150) | 0.027 | 0.002 | 21699.7 | 0.112 |

## H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.606 | [0.472, 0.740] | 30 | 5 | refuted (underpowered) |
| H2 | repair rounds, zehn - python_strict | 0.933 | [0.607, 1.280] | 30 | 5 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | -0.020 | [-0.067, 0.013] | 30 | 5 | inconclusive (underpowered) |
| H4 | total tokens, zehn - python_strict | 18602.840 | [14589.967, 22887.460] | 30 | 5 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | -0.013 | [-0.040, 0.013] | 30 | 5 | inconclusive (underpowered) |

The verdict column is `report.py`'s mechanical label. Every row is `(underpowered)` (the rule asks for at least 150 tasks and 5 repeats), and a label such as the one on H1, H2 or H4 only says the interval lies on the wrong side of that row's threshold; with 30 tasks it is not a refutation in the sense of roadmap section 14.

- **H1** (first-try ratio): 0.606, CI [0.472, 0.740]; the support threshold is a CI lower bound of 0.8, and the whole interval is below it.
- **H2** (repair rounds): zehn needs 0.933 more rounds than python_strict, CI [0.607, 1.280].
- **H3** (silent bugs): difference -0.020, CI [-0.067, 0.013]; the interval contains 0.
- **H4** (tokens): zehn uses 18602.840 more tokens per run than python_strict, CI [14589.967, 22887.460]. The Zehn prompt carries `SPEC.md` on every round.
- **H5** (pass_repair vs rust_strict): -0.013, CI [-0.040, 0.013]; the interval contains 0.

Where H5 comes from. 4 of 30 tasks differ between zehn and rust_strict in pass_repair; the other tasks are equal:

| task | zehn | rust_strict | zehn - rust_strict |
|---|---|---|---|
| domain_004 | 0.800 | 1.000 | -0.200 |
| effect_004 | 0.600 | 0.400 | 0.200 |
| pure_005 | 0.800 | 1.000 | -0.200 |
| text_001 | 0.800 | 1.000 | -0.200 |

A one-run swing in one task (one repeat of 5) moves this gap by 0.007.

First-try failures of zehn: 64 of 150 runs. Diagnostic codes present in the round-1 feedback (a run can have several): E0201 in 46, E0602 in 10, E0308 in 3. `E0201` is a parse error, per the EXPLAIN table in `zehn.py`.

## Per category

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| domain | python_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| domain | rust | default | 6 | 30 | 0.967 | 1.000 | 0.000 |
| domain | rust_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| domain | ts_strict | default | 6 | 30 | 0.667 | 1.000 | 0.000 |
| domain | zehn | default | 6 | 30 | 0.333 | 0.967 | 0.000 |
| edit | python_plain | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| edit | python_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| edit | rust | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| edit | rust_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| edit | ts_strict | default | 6 | 30 | 0.833 | 1.000 | 0.000 |
| edit | zehn | default | 6 | 30 | 0.933 | 1.000 | 0.000 |
| effect | python_plain | default | 6 | 30 | 0.733 | 0.733 | 0.267 |
| effect | python_strict | default | 6 | 30 | 0.767 | 0.767 | 0.233 |
| effect | rust | default | 6 | 30 | 0.800 | 0.800 | 0.200 |
| effect | rust_strict | default | 6 | 30 | 0.833 | 0.833 | 0.167 |
| effect | ts_strict | default | 6 | 30 | 0.367 | 0.733 | 0.267 |
| effect | zehn | default | 6 | 30 | 0.400 | 0.867 | 0.100 |
| pure | python_plain | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| pure | python_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| pure | rust | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| pure | rust_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| pure | ts_strict | default | 6 | 30 | 0.400 | 1.000 | 0.000 |
| pure | zehn | default | 6 | 30 | 0.633 | 0.967 | 0.000 |
| text | python_plain | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| text | python_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| text | rust | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| text | rust_strict | default | 6 | 30 | 1.000 | 1.000 | 0.000 |
| text | ts_strict | default | 6 | 30 | 0.633 | 1.000 | 0.000 |
| text | zehn | default | 6 | 30 | 0.567 | 0.967 | 0.033 |

`effect` is the only category where pass_repair of the non-Zehn languages is below 1.0: python_plain 0.733, python_strict 0.767, rust 0.800, rust_strict 0.833, ts_strict 0.733; zehn 0.867. In the other four categories every non-Zehn language except ts_strict is at or near its ceiling on the first try.

## Threats to validity

1. **Reference solutions by Claude.** The 30 reference solutions were written by Claude: contamination and style bias are possible in both directions.
2. **Selection bias in favour of Zehn.** Every task was chosen to be expressible in Zehn v0.3.
3. **Too few tasks.** 30 tasks cannot support the section 14 refutation rule; report.py itself calls every row underpowered (minimum 150 tasks, 5 repeats).
4. **One model, one temperature (1.0).** A different model could move the ceilings and the gap.
5. **Ceiling effects.** 25 of the 30 tasks have pass_repair 1.0 in all six languages, so the pass_repair comparison (H5) rests on 4 tasks (see the table under H5).
6. **SPEC size and the 5,000-token cap.** `SPEC.md` is about 3,000 words, an estimate of 4,200 to 5,600 tokens (no tokenizer was available; **[UNVERIFIED]** by the API token-count endpoint). The provider-reported round-1 input of zehn runs is a minimum of 5900 tokens against 475 for python_plain (mean 6170 against 685); the difference (5425 by minimum, 5485 by mean) also contains the protocol text and any task-text difference, and it is measured with Gemma's tokenizer, not the one the cap is defined for. It does not settle whether `SPEC.md` fits the cap.
7. **Adapters differ.** Each language has its own tool loop and feedback richness. The zehn adapter forgives layout-only errors (ADR-0014); whether the `python_strict`, `ts_strict` and `rust_strict` adapters hold an equivalent asymmetry is listed as unreviewed in STATE.md. One zehn run (pure_005, repeat 3) ended its last two rounds on E0203 alone; the adapter accepts a layout-only candidate only when the `zehn fmt` output re-checks clean, so formatting or the re-check failed there. The cause was not investigated.
8. **Possible task defects.** effect_004 and effect_006 stay below 1.0 pass_repair for rust_strict and other languages, so a defect in the hidden tests or the statement is possible. **[UNVERIFIED]**: nobody has inspected those tests for this report.
9. **Run counts.** Valid runs per language: python_plain 150, python_strict 150, rust 150, rust_strict 150, ts_strict 150, zehn 150. They are equal, so no language is favoured by exclusions.
10. **Stability.** Tasks whose first-try result varies across the 5 repeats (stability / tasks with variance > 0): zehn 0.112 / 17; python_plain 0.008 / 1; python_strict 0.013 / 2; ts_strict 0.144 / 20; rust 0.011 / 2; rust_strict 0.016 / 2. Task-level numbers for ts_strict and zehn are noisy.

## Calibration for growth

**Floors and ceilings (pass@1; floor < 0.1, ceiling > 0.95).** Per language: zehn 0.573; python_plain 0.947; python_strict 0.953 (ceiling); ts_strict 0.580; rust 0.953 (ceiling); rust_strict 0.967 (ceiling).

Per category and language, ceilings: domain/python_plain, domain/python_strict, domain/rust, domain/rust_strict, edit/python_plain, edit/python_strict, edit/rust, edit/rust_strict, pure/python_plain, pure/python_strict, pure/rust, pure/rust_strict, text/python_plain, text/python_strict, text/rust, text/rust_strict. Floors: none.

Per task and language, floors (pass@1 < 0.1): domain_003/zehn, domain_005/zehn, effect_004/ts_strict, effect_004/rust, effect_006/zehn, effect_006/python_plain, effect_006/ts_strict, pure_005/zehn, text_005/zehn. Number of tasks at the pass@1 ceiling per language: zehn 8, python_plain 28, python_strict 28, ts_strict 8, rust 27, rust_strict 28.

Tasks by solving (final_pass, from the report's Calibration section):

- Tasks no language solved (0): none
- Tasks every language solved (25): domain_001, domain_002, domain_003, domain_005, domain_006, edit_001, edit_002, edit_003, edit_004, edit_005, edit_006, effect_001, effect_002, effect_003, effect_005, pure_001, pure_002, pure_003, pure_004, pure_006, text_002, text_003, text_004, text_005, text_006
- Tasks with pass_repair 1.0 in all six languages (25): domain_001, domain_002, domain_003, domain_005, domain_006, edit_001, edit_002, edit_003, edit_004, edit_005, edit_006, effect_001, effect_002, effect_003, effect_005, pure_001, pure_002, pure_003, pure_004, pure_006, text_002, text_003, text_004, text_005, text_006

**Tasks needed for a 95% CI half-width of 0.08 on a paired difference.** n = (1.96 x SD / 0.08)^2, with SD the observed standard deviation of the per-task paired differences (repeats averaged first). Observed half-width of H5 at 30 tasks: 0.026.

| contrast (a - b) | metric | mean diff | SD of per-task diffs | tasks with diff != 0 | tasks needed |
|---|---|---|---|---|---|
| zehn - rust_strict | pass_repair | -0.013 | 0.073 | 4 of 30 | 4 |
| zehn - rust_strict | pass_at_1 | -0.393 | 0.373 | 22 of 30 | 84 |
| zehn - python_strict | pass_repair | 0.000 | 0.105 | 5 of 30 | 7 |
| zehn - python_strict | pass_at_1 | -0.380 | 0.373 | 22 of 30 | 84 |
| zehn - python_plain | pass_repair | 0.007 | 0.134 | 5 of 30 | 11 |
| zehn - python_plain | pass_at_1 | -0.373 | 0.378 | 21 of 30 | 86 |

Reading: for pass_repair the target half-width is already met at 30 tasks (the table asks for far fewer), because the differences sit in a handful of tasks and the rest are exactly 0. That SD is not stable: it comes from a few non-zero tasks and changes with every task added, so this number must not be used to stop growing. For pass@1 the observed spread asks for about 84 to 86 tasks, which the planned growth to 100 covers. The requirement that actually binds is section 14's refutation rule (which is not in this repository) and `report.py`'s own minimum of 150 tasks: 100 development tasks alone stay `(underpowered)` under that rule.

**Quotas for growth to 100 development tasks.** Tasks per category that separate languages today:

| category | tasks now | tasks where any language has pass_repair < 1 | tasks where any language has pass@1 < 1 |
|---|---|---|---|
| domain | 6 | 1 | 6 |
| edit | 6 | 0 | 2 |
| effect | 6 | 2 | 6 |
| pure | 6 | 1 | 6 |
| text | 6 | 1 | 5 |

| category | now | plan adds | proposed adds | total after (proposed) |
|---|---|---|---|---|
| domain | 6 | +11 | +11 | 17 |
| edit | 6 | +26 | +11 | 17 |
| effect | 6 | +11 | +26 | 32 |
| pure | 6 | +11 | +11 | 17 |
| text | 6 | +11 | +11 | 17 |
| total | 30 | +70 | +70 | 100 |

Why the proposal differs from the plan: `edit` has 0 of 6 tasks where any language is below 1.0 in pass_repair and every language reaches pass_repair 1.0 in that category, so 26 more of them would add the least information about H5; `effect` is the only category with headroom for the strongest competitors, so it gets the 26 and `edit` the 11. `pure`, `text` and `domain` keep +11: each has 1, 1 and 1 of 6 tasks that separate languages in pass_repair, and they carry the first-try gap that drives H1, H2 and H4. Caveats: this rests on one model, whose ceilings may move with another model; effect_004 and effect_006 may be defective tasks (Threats, item 8) and should be reviewed before more tasks are copied from their pattern; whether 26 new effect tasks can be authored without repeating patterns is unknown **[UNVERIFIED]**. The change is a judgment from one model's ceilings; keeping the plan's split is defensible, but the added edit tasks are then expected to sit at the ceiling for this model.

New tasks should be harder, not more numerous in the easy categories: aim for pass_repair between about 0.5 and 0.9 for the strongest non-Zehn language, since rust_strict is at 0.967 over all tasks.

Computation (run from the project root; `bench/benchlib` only, nothing was added to the repository): the helper functions `floors_ceilings_*`, `task_lang_flags`, `paired_series` and `n_needed` take records.jsonl without errored runs, `metrics.run_pass1` / `metrics.run_pass_repair` per run, `metrics.task_series` per task, and `n_needed` is `ceil((1.96 * sd / 0.08) ** 2)` with `sd` the sample standard deviation (n - 1).

## Gate recommendation

Rule (roadmap section 3.6): if the H5 point estimate is worse than the `rust_strict` branch, the recommendation is "stop Phase 1, apply section 14"; otherwise "continue".

Result: H5 = -0.013, CI [-0.040, 0.013], GATE line printed by report.py. **Recommendation: stop Phase 1, apply section 14.**

Facts the builder should weigh (the rule does not): the CI contains 0; the gap is 7 versus 5 failed runs of 150; it comes from 4 tasks; every verdict is `(underpowered)`; Zehn's first-try gap and token cost are large (H1, H2, H4) but are not what the rule tests. This is a proposal: the builder takes the decision. ADR-0016 records it with `Status: proposed`.
