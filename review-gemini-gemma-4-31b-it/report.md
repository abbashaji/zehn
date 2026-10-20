# Review experiment (Bet 1)

run: `bench/results/review-gemini-gemma-4-31b-it`, records: 5

| arm | runs | accuracy | defect found | defect located | false alarm | unanswered | tokens/run |
|---|---|---|---|---|---|---|---|
| zehn | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 1315 |
| python | 1 | 0.000 | 0.000 | 0.000 | nan | 1 | 997 |
| python_examples | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 1148 |

Paired by task (accuracy = mean of defect-found and clean-called-correct), 95% CI, 10,000 resamples:

| comparison | tasks | accuracy diff | 95% CI | verdict |
|---|---|---|---|---|
| zehn - python | 0 | +nan | [+nan, +nan] | no clear difference |
| zehn - python_examples | 1 | +0.000 | [+0.000, +0.000] | no clear difference |
| python_examples - python | 0 | +nan | [+nan, +nan] | no clear difference |

Rule: Zehn wins only if the CI of `zehn - python_examples` excludes 0 in its favour (the control that also shows examples). Runs with fewer than 50 tasks or 5 repeats are underpowered.
