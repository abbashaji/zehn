# Experiment: review (Bet 1 of docs/WINNING_ANGLES.md)

Question: can a reviewer find a planted defect, and is Zehn easier to review than Python?
378 items = 63 tasks x 3 arms x (1 defective + 1 clean program). Arms: `zehn` (reference solution with its
intent, contracts and examples), `python` (same task, plain code), `python_examples` (python plus the visible
examples as comments; the control that separates "has examples" from "is Zehn").

A planted defect is a one-edit mutation of the reference body (operator, boundary, constant, logic), kept only
if it survives the program's own check (`tool_check` ok: Zehn runs examples and contracts) and fails a hidden
test. Per task the Zehn mutant is drawn first and the Python mutants prefer the same class (paired design).
Tasks without a surviving defect in every arm are dropped (37 of 100).

```
python3 bench/review.py make --out bench/experiments/review/items.json     # already committed; deterministic
python3 bench/review.py run --items bench/experiments/review/items.json --model gemini:gemma-4-31b-it --repeats 5 --run-id review-1 --yes
python3 bench/review.py report --run bench/results/review-1
```

Or dispatch the workflow `review` (one model, resumes by itself).

Decision rule (fixed before the run): Zehn wins only if the paired 95% CI of `zehn - python_examples` accuracy
excludes 0 in Zehn's favour. A CI that includes 0 means no evidence; a result with 3 repeats or one model is
labelled underpowered. Limitations: the reviewer is a model, not a human; the Zehn arm also gets a 90-word
reading guide; defects are mechanical mutations, not natural mistakes; the reviewer cannot run anything.
