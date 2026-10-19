# A/B comparison

A = effect_examples-gemini-gemma-4-31b-it-a, B = effect_examples-gemini-gemma-4-31b-it-b, simpler option = a
Paired over tasks (repeats, models and cells averaged first); difference = A - B; 10000 resamples, seed 1234, 95% CI.

| metric | A | B | A - B | 95% CI | tasks |
|---|---|---|---|---|---|
| pass@1 | 0.284 | 0.276 | 0.008 | [-0.106, 0.128] | 17 |
| pass_repair | 0.706 | 0.740 | -0.034 | [-0.111, 0.041] | 17 |
| repair rounds | 2.260 | 1.665 | 0.595 | [0.268, 0.931] | 17 |
| silent-bug rate | 0.142 | 0.100 | 0.042 | [-0.030, 0.118] | 17 |
| hallucination rate | 0.017 | 0.000 | 0.017 | [0.000, 0.037] | 17 |
| total tokens | 45159.7 | 37190.9 | 7968.8 | [2828.1, 13091.9] | 17 |
| stability | 0.067 | 0.123 | -0.056 | [-0.107, -0.008] | 17 |

DECISION: keep a
