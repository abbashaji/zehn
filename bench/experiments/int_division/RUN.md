# Experiment: Int division (roadmap section 5, item 3)

Question: does forbidding the operators `/` and `%` on Int (dialect `int_ops=explicit`, you write
`int.div_floor`, `int.div_trunc`, `int.rem_euclid`) change how often a model gets integer division right,
compared with the v0.3 default (`/` and `%` with floor semantics)?

- A = `default` (operators allowed), B = `int_ops=explicit` (operators are `E0312`). `simpler` = `a`:
  when the CI of the difference includes 0, keep A.
- 50 tasks: the first 30 dev tasks (`pure_001-006`, `text_001-006`, `domain_001-006`, `effect_001-006`,
  `edit_001-006`) as a control, plus `numneg_001..020` (hidden tests with negative operands; the description
  states the rounding in words: 8 floor, 6 toward zero, 6 non-negative remainder). The numneg tasks carry
  category `pure` in `task.json`; their ids do not follow the `<category>_<NNN>` rule, which the loader allows
  for any task root below a folder named `experiments`.
- The decision is taken in TASK_08. This pack only prepares it; no run has been made.

## Commands (run from the project root)

```
ONLY=$(python3 -c "import json;print(','.join(json.load(open('bench/experiments/int_division/experiment.json'))['only']))")
COMMON="--lang zehn --tasks-dir bench/tasks --tasks-dir bench/experiments/int_division/tasks --only $ONLY --repeats 5"
MODEL=gemini:gemma-4-31b-it        # any one model spec; one run never mixes models

python3 bench/run.py run $COMMON --models $MODEL --variant default           --run-id intdiv-a --dry-run
python3 bench/run.py run $COMMON --models $MODEL --variant int_ops=explicit  --run-id intdiv-b --dry-run

python3 bench/run.py run $COMMON --models $MODEL --variant default           --run-id intdiv-a --yes
python3 bench/run.py run $COMMON --models $MODEL --variant int_ops=explicit  --run-id intdiv-b --yes
# interrupted? add --resume to the same command

python3 bench/report.py ab --a bench/results/intdiv-a --b bench/results/intdiv-b --simpler a --out bench/results/intdiv-ab.md
```

Use the same model, `--repeats` and `--temperature` for both runs. `--yes` is required for remote models and
costs money (or free-tier quota).

## Expected counts

Each `--dry-run` prints `runs: 250 (50 tasks x 1 langs x 1 models x 5 repeats)` and `worst-case API calls:
1250` (250 runs x 5 rounds). Both variants together: 500 runs, at most 2,500 calls. Realistic calls are
fewer (a run stops at its first accepted passing round); the README's planning figure of about 2 rounds per
run gives about 500 calls per variant, about 1,000 in total. That figure is an estimate, not a measurement.
With one model on the free Gemini tier, read `bench/README.md` ("Running the baseline for free") for the
tokens-per-minute arithmetic; the Zehn prompt grows by under 200 words in B.

## Checks before spending anything

```
python3 bench/run.py verify-refs --lang zehn,python_plain --tasks-dir bench/experiments/int_division/tasks
python3 bench/run.py verify-refs --lang zehn --variant int_ops=explicit --tasks-dir bench/experiments/int_division/tasks
```

Both print `OK` for all 20 tasks (the refs are written with the three new functions, so they are valid
in both dialects).

## Known limits of this design

- 6 of the 30 control tasks have a `ref.zehn` that uses `/` or `%` (domain_005, edit_002, pure_002,
  pure_004, pure_006, text_006), so `verify-refs --variant int_ops=explicit --tasks-dir bench/tasks` fails
  for them and `stub:perfect` under B fails them too. Real model runs are not affected, but in B those
  tasks also test whether the model avoids the operators; `bench/tasks/` must not change in this task.
- The control tasks mostly use positive operands (`bench/README.md`: tests never divide with a negative
  operand), so a difference on them comes from the new names and the `E0312` repair round, not rounding.
- A floor remainder has no explicit name. `int.rem_euclid` equals `%` only for a positive divisor, so
  tasks that need a remainder with the sign of the divisor or dividend must compute `a - b * q`
  (numneg_003, 010, 014). That is part of what B measures.
- numneg descriptions state the rounding in words on purpose: the test measures following the stated
  rule, not guessing the language's default. Whether a model picks the right function name is a separate
  effect from whether it knows the semantics; the A/B cannot separate them.
- One model, 5 repeats, 50 tasks: expect wide CIs; `report.py ab` labels the result, do not read more.
