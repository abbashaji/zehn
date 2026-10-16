# ADR-0019 Examples of effectful functions get an in-language mock handler (option A)
Status: unmeasured

## Problem
In v0.3 an effectful function cannot have an example: a call to it from an example is `E0602`. `--strict` requires every function to have an example (`E0402`). So under `--strict` an effectful function can only be "covered" by examples of its pure helpers, and its own behaviour is never exercised. The reference solutions of the benchmark category `effect` do exactly that.

## Options
A. Mock handler: an example may carry `with <effect> = mock [results]` and `prints [texts]`; the effect is simulated, the host is never touched (flag `effect_examples=mock`).
B. Strict only for pure functions: `--strict` stops asking effectful functions for examples (no new syntax).
C. No examples for effects: keep `E0602` and say so in the spec; `E0402` is waived by the language, not by a rule about purity.

## Experiment run (or why none)
None. The prototype and the experiment are built (`bench/experiments/effect_examples/`, variant text `bench/variants/effect_examples=mock.md`); nothing was run (no API key in the build sandbox). Two gaps in `bench/` (read-only for this task) must be fixed before the run is meaningful: the adapter's `fmt` call and the hidden-test runner ignore the dialect, so a mock clause is a parse error there (see RUN.md).

## Numeric result
None. Facts measured while building: all 101 reference solutions give identical `check --strict --json` output under both dialects; the literal strict rule below would fail 17 of them (all 17 `effect` tasks, 38 effectful functions).

## Decision
Build A first because it is the only option that changes what a model can say: B and C remove a requirement, A lets the requirement be met by a test of the effectful behaviour itself, and it keeps the language's claim that every function has an executable example. Whether that is worth the extra syntax, the three error codes and the longer prompt is unmeasured; the decision stays open until the A/B runs (`simpler` is `a`, the default dialect).

Choices made while building, all revisable:
- Unit has no literal, so `console` mock lists are `[]` and Unit effects never use up results; an example with mock clauses may have type `Unit` (a bare call), otherwise a `-> Unit` function could not have an example at all.
- Strict rule: a mocked example counts as an example, an unmocked one still counts. The literal reading ("an effectful function satisfies the rule only through a mocked example") is the switch `STRICT_NEEDS_MOCKED_EXAMPLE` in `zehnlib/passes/effect_examples.py`, off by default, because it breaks the task's own requirement that the reference solutions pass unchanged. With the default, `--strict` pressure towards mocked examples is absent; the experiment then measures availability, not obligation.
- The coverage check (E0605) is the static pass `effect_examples` at order 420 (moved there by the merge TASK_06m; in the branch it ran at the end of the `names` pass). This ADR was written as ADR-0015, a number `ADR-0015-api-failures-are-not-model-failures.md` already uses; the merge renumbered it to 0019.
- Mock results that are never used are not an error.

## Revisit condition
After the A/B: keep A if B beats A on the `effect` pass rate by more than the run-to-run spread of A (the 5 repeats), and the extra prompt text and rounds are not what produced the gain; otherwise fall back to B or C. Revisit the strict switch when the experiment can show whether obligation, not availability, drives the effect.
