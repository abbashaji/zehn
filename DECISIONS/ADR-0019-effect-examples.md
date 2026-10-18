# ADR-0019 Examples of effectful functions get an in-language mock handler (option A)
Status: measured

## Problem
In v0.3 an effectful function cannot have an example: a call to it from an example is `E0602`. `--strict` requires every function to have an example (`E0402`). So under `--strict` an effectful function can only be "covered" by examples of its pure helpers, and its own behaviour is never exercised. The reference solutions of the benchmark category `effect` do exactly that.

## Options
A. Mock handler: an example may carry `with <effect> = mock [results]` and `prints [texts]`; the effect is simulated, the host is never touched (flag `effect_examples=mock`).
B. Strict only for pure functions: `--strict` stops asking effectful functions for examples (no new syntax).
C. No examples for effects: keep `E0602` and say so in the spec; `E0402` is waived by the language, not by a rule about purity.

## Experiment run (or why none)
Run on 2026-10-17/18 with the workflow `.github/workflows/experiments.yml` (`bench/experiments/effect_examples/`): model `gemini:gemma-4-31b-it` (free tier), 17 `effect` tasks, A = `default`, B = `effect_examples=mock`, `simpler` = `a`. The planned 5 repeats were cut to 3 for time (free-tier server errors: about 40% of the runs of the first dispatch ended in a server error and were redone by `--resume`). All 51 runs per side are complete for repeats 1 to 3; the report also holds the extra repeats that had finished (A 54 runs, B 75 runs in total). Report: `effect_examples-gemini-gemma-4-31b-it-ab.md` on the branch `bench-experiments`.

Two things went wrong in the first attempts and were fixed before the numbers below: the adapter ignored the dialect (see the old RUN.md note), and SPEC.md, the base of the system prompt, documented the mock syntax for both sides, so side A wrote `with ... = mock` and the default parser rejected it (E0201 in 37 of 43 runs). The adapter now removes that subsection unless the variant is `effect_examples=mock`. All results from before that fix were discarded.

## Numeric result
Paired over the 17 tasks, difference = A - B, 95% CI from 10,000 resamples (`report.py ab`):

| metric | A (default) | B (mock) | A - B | 95% CI |
|---|---|---|---|---|
| pass@1 | 0.284 | 0.276 | +0.008 | [-0.106, 0.128] |
| pass_repair | 0.706 | 0.740 | -0.034 | [-0.111, 0.041] |
| repair rounds | 2.260 | 1.665 | +0.595 | [0.268, 0.931] |
| silent-bug rate | 0.142 | 0.100 | +0.042 | [-0.030, 0.118] |
| total tokens | 45,160 | 37,191 | +7,969 | [2,828, 13,092] |

`report.py` says `DECISION: keep a` (the pass_repair CI includes 0). Restricted to exactly 3 repeats per side the picture is the same (pass_repair 0.706 vs 0.765, CI [-0.157, 0.039]). Per task, B is ahead on 5 tasks, A on 3, 9 tie; `effect_008` and `effect_016` are never solved by either side. Limits: one model, 17 tasks, 3 repeats, so the CIs are wide; B's prompt is longer, yet its runs used fewer tokens.

Earlier facts, measured while building: all 101 reference solutions give identical `check --strict --json` output under both dialects; the literal strict rule below would fail 17 of them (all 17 `effect` tasks, 38 effectful functions).

## Decision
Build A first because it is the only option that changes what a model can say: B and C remove a requirement, A lets the requirement be met by a test of the effectful behaviour itself, and it keeps the language's claim that every function has an executable example. Whether that is worth the extra syntax, the three error codes and the longer prompt was measured once (see Numeric result): no clear gain in correctness, a clear gain in repair rounds and tokens.

Outcome of the A/B: the revisit condition below is not met, so the mock dialect is not promoted; the flag `effect_examples` stays `off` by default. The experiment did not test options B and C of this ADR, so the choice between them (or keeping A behind the flag) is still open.

Choices made while building, all revisable:
- Unit has no literal, so `console` mock lists are `[]` and Unit effects never use up results; an example with mock clauses may have type `Unit` (a bare call), otherwise a `-> Unit` function could not have an example at all.
- Strict rule: a mocked example counts as an example, an unmocked one still counts. The literal reading ("an effectful function satisfies the rule only through a mocked example") is the switch `STRICT_NEEDS_MOCKED_EXAMPLE` in `zehnlib/passes/effect_examples.py`, off by default, because it breaks the task's own requirement that the reference solutions pass unchanged. With the default, `--strict` pressure towards mocked examples is absent; the experiment then measures availability, not obligation.
- The coverage check (E0605) is the static pass `effect_examples` at order 420 (moved there by the merge TASK_06m; in the branch it ran at the end of the `names` pass). This ADR was written as ADR-0015, a number `ADR-0015-api-failures-are-not-model-failures.md` already uses; the merge renumbered it to 0019.
- Mock results that are never used are not an error.

## Revisit condition
After the A/B: keep A if B beats A on the `effect` pass rate by more than the run-to-run spread of A (the 5 repeats), and the extra prompt text and rounds are not what produced the gain; otherwise fall back to B or C. Revisit the strict switch when the experiment can show whether obligation, not availability, drives the effect.
