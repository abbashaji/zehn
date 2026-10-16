# A/B comparison

A = int_division-gemini-gemma-4-31b-it-a, B = int_division-gemini-gemma-4-31b-it-b, simpler option = a
Paired over tasks (repeats, models and cells averaged first); difference = A - B; 10000 resamples, seed 1234, 95% CI.

| metric | A | B | A - B | 95% CI | tasks |
|---|---|---|---|---|---|
| pass@1 | 0.500 | 0.500 | 0.000 | [0.000, 0.000] | 2 |
| pass_repair | 1.000 | 0.500 | 0.500 | [0.000, 1.000] | 2 |
| repair rounds | 0.500 | 2.500 | -2.000 | [-3.000, -1.000] | 2 |
| silent-bug rate | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 2 |
| hallucination rate | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 2 |
| total tokens | 18945.5 | 9669.5 | 9276.0 | [-10118.0, 28670.0] | 2 |
| stability | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 2 |

DECISION: keep a
