# A/B comparison

A = int_division-gemini-gemma-4-31b-it-a, B = int_division-gemini-gemma-4-31b-it-b, simpler option = a
Paired over tasks (repeats, models and cells averaged first); difference = A - B; 10000 resamples, seed 1234, 95% CI.

| metric | A | B | A - B | 95% CI | tasks |
|---|---|---|---|---|---|
| pass@1 | 0.707 | 0.713 | -0.007 | [-0.093, 0.073] | 50 |
| pass_repair | 0.947 | 0.947 | 0.000 | [-0.053, 0.047] | 50 |
| repair rounds | 0.660 | 0.987 | -0.327 | [-0.520, -0.127] | 50 |
| silent-bug rate | 0.027 | 0.007 | 0.020 | [-0.013, 0.067] | 50 |
| hallucination rate | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 50 |
| total tokens | 18177.8 | 23386.9 | -5209.1 | [-7371.9, -3074.9] | 50 |
| stability | 0.071 | 0.053 | 0.018 | [-0.009, 0.044] | 50 |

DECISION: keep a
