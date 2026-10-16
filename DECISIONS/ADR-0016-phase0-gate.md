# ADR-0016 Phase 0 gate: recommendation from the gemma-4-31b-it baseline
Status: proposed

## Problem
(Numbered 0016 because ADR-0014 and ADR-0015 already exist; TASK_03 named this file ADR-0014-phase0-gate.md.)

The Phase 0 baseline (30 tasks x 6 languages x 5 repeats on `gemini:gemma-4-31b-it`) is in `bench/results/baseline-gemini-gemma-4-31b-it/` and is written up in `bench/BASELINE_v0.3.md`. Roadmap section 3.6 turns the H5 estimate into a gate; the builder must decide whether Phase 1 continues.

## Options
1. Continue Phase 1.
2. Stop Phase 1 and apply roadmap section 14 (the rule's output when H5 is worse than rust_strict - fired here).
3. Top up or widen the baseline first (more tasks, another model) and decide afterwards.

## Experiment run (or why none)
`python3 bench/report.py --run bench/results/baseline-gemini-gemma-4-31b-it --exclude-errors --out bench/BASELINE_v0.3.md`. Zehn sha256 `0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73` (identical to the current `zehn.py`). Errored records: 0 of 900 (none left in `records.jsonl`). Every verdict is `(underpowered)`; with 30 tasks nothing can be refuted in the sense of section 14.

## Numeric result

| H | estimate | 95% CI | report.py label |
|---|---|---|---|
| H1 | 0.606 | [0.472, 0.740] | refuted (underpowered) |
| H2 | 0.933 | [0.607, 1.280] | refuted (underpowered) |
| H3 | -0.020 | [-0.067, 0.013] | inconclusive (underpowered) |
| H4 | 18602.840 | [14589.967, 22887.460] | refuted (underpowered) |
| H5 | -0.013 | [-0.040, 0.013] | inconclusive (underpowered) |

pass@1: zehn 0.573, python_plain 0.947, rust_strict 0.967. pass_repair: zehn 0.953, python_plain 0.947, rust_strict 0.967. Failed pass_repair runs: zehn 7 of 150, rust_strict 5 of 150; the H5 gap comes from 4 tasks.

## Decision
Proposed, not taken: **stop Phase 1, apply section 14** (the roadmap's rule applied to the H5 point estimate -0.013). The builder decides; the CI [-0.040, 0.013] contains 0 and the gap is small, so a builder who prefers option 3 has data to support it. Proposed growth of the task set: see "Calibration for growth" in `bench/BASELINE_v0.3.md` (effect +26, edit +11 instead of the plan's +11 and +26).
