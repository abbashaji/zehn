# Experiment: effect_examples (ADR-0019, status unmeasured)

A = `default` (v0.3: effectful functions cannot have an example), B = `effect_examples=mock`
(mocked examples). Task set: the 17 tasks of category `effect`, 5 repeats each, model
`gemini:gemma-4-31b-it` (the baseline model, so the numbers are comparable). Simpler option: A.

## Before the first run: two gaps in `bench/` (read-only for this task, listed in the summary)

1. `bench/benchlib/adapters/zehn.py`, `_canonical`: `zehn fmt` is called without the `--dialect`
   arguments, so ADR-0014's layout forgiveness cannot work for a B program (fmt fails with `E0201`).
2. `bench/benchlib/adapters/_zehn_runner.py` (and the command in `zehn.py` that starts it, which
   passes no dialect): `parse(src)` runs under the default dialect, so every B program that uses a mock
   clause fails its hidden tests with `E0201` even when `zehn check` passed it.

Until both are fixed B is scored against a parser that rejects the very syntax it is testing.

## Commands

```
python3 bench/run.py run --models gemini:gemma-4-31b-it --lang zehn --tasks-dir bench/tasks --only effect_001,effect_002,effect_003,effect_004,effect_005,effect_006,effect_007,effect_008,effect_009,effect_010,effect_011,effect_012,effect_013,effect_014,effect_015,effect_016,effect_017 --repeats 5 --variant default --run-id effect_examples-a --yes

python3 bench/run.py run --models gemini:gemma-4-31b-it --lang zehn --tasks-dir bench/tasks --only effect_001,effect_002,effect_003,effect_004,effect_005,effect_006,effect_007,effect_008,effect_009,effect_010,effect_011,effect_012,effect_013,effect_014,effect_015,effect_016,effect_017 --repeats 5 --variant effect_examples=mock --run-id effect_examples-b --yes

python3 bench/report.py ab --a bench/results/effect_examples-a --b bench/results/effect_examples-b --simpler a --out bench/experiments/effect_examples/REPORT.md
```

An interrupted run continues with the same command plus `--resume`. The text appended to B's
system prompt is `bench/variants/effect_examples=mock.md`. The reference solutions need no change
(checked: `check --strict --json` of all 101 `ref.zehn` is byte-identical under both dialects).
