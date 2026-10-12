# Benchmark report

## Runs

| dir | run_id | set | records | tasks | meta |
|---|---|---|---|---|---|
| pilot-gemini-gemma-4-31b-it | pilot-gemini-gemma-4-31b-it | dev | 36 | 6 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'pilot-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,domain_005,edit_003,effect_004,pure_002,text_001 '], date_utc=2026-10-12T18:34:01Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_005', 'edit_003', 'effect_004', 'pure_002', 'text_001'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b | - | - | 0 | 0 | api_hosts={'gemini:gemma-4-31b': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b', '--run-id', 'pilot-gemini-gemma-4-31b', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,edit_001,effect_001,pure_001,text_004,effect_004'], date_utc=2026-10-12T18:16:43Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'edit_001', 'effect_001', 'effect_004', 'pure_001', 'text_004'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |

max_rounds used for censoring: 5
Bootstrap: 10000 resamples over tasks, seed 1234, 95% percentile interval.

## Results per language, variant and model

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 6 | 6 | 1.000 | 1.000 | 0.000 (censored 0/6) | 0.000 | n/a | 2443.5 | 0.000 |
| python_strict | default | gemini:gemma-4-31b-it | 6 | 6 | 1.000 | 1.000 | 0.167 (censored 0/6) | 0.000 | 0.000 | 3557.5 | 0.000 |
| rust | default | gemini:gemma-4-31b-it | 6 | 6 | 0.833 | 0.833 | 0.000 (censored 0/6) | 0.167 | n/a | 2152.5 | 0.000 |
| rust_strict | default | gemini:gemma-4-31b-it | 6 | 6 | 0.833 | 0.833 | 0.000 (censored 0/6) | 0.167 | n/a | 2713.7 | 0.000 |
| ts_strict | default | gemini:gemma-4-31b-it | 6 | 6 | 0.667 | 0.833 | 0.167 (censored 0/6) | 0.167 | 1.000 | 3037.3 | 0.000 |
| zehn | default | gemini:gemma-4-31b-it | 6 | 6 | 0.667 | 0.667 | 1.833 (censored 2/6) | 0.000 | 0.000 | 30902.3 | 0.000 |

## Per category (models pooled)

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 2 | 2 | 1.000 | 1.000 | 0.000 |
| domain | python_strict | default | 2 | 2 | 1.000 | 1.000 | 0.000 |
| domain | rust | default | 2 | 2 | 1.000 | 1.000 | 0.000 |
| domain | rust_strict | default | 2 | 2 | 1.000 | 1.000 | 0.000 |
| domain | ts_strict | default | 2 | 2 | 0.500 | 1.000 | 0.000 |
| domain | zehn | default | 2 | 2 | 0.500 | 0.500 | 0.000 |
| edit | python_plain | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| edit | python_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| edit | rust | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| edit | rust_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| edit | ts_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| edit | zehn | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| effect | python_plain | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| effect | python_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| effect | rust | default | 1 | 1 | 0.000 | 0.000 | 1.000 |
| effect | rust_strict | default | 1 | 1 | 0.000 | 0.000 | 1.000 |
| effect | ts_strict | default | 1 | 1 | 0.000 | 0.000 | 1.000 |
| effect | zehn | default | 1 | 1 | 0.000 | 0.000 | 0.000 |
| pure | python_plain | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| pure | python_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| pure | rust | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| pure | rust_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| pure | ts_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| pure | zehn | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| text | python_plain | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| text | python_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| text | rust | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| text | rust_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| text | ts_strict | default | 1 | 1 | 1.000 | 1.000 | 0.000 |
| text | zehn | default | 1 | 1 | 1.000 | 1.000 | 0.000 |

## Hypotheses H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.667 | [0.333, 1.000] | 6 | 1 | inconclusive (underpowered) |
| H2 | repair rounds, zehn - python_strict | 1.667 | [0.667, 2.833] | 6 | 1 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | 0.000 | [0.000, 0.000] | 6 | 1 | refuted (underpowered) |
| H4 | total tokens, zehn - python_strict | 27344.833 | [13530.000, 42208.500] | 6 | 1 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | -0.167 | [-0.500, 0.000] | 6 | 1 | refuted (underpowered) |

Underpowered = fewer than 150 tasks or fewer than 5 repeats (smallest (task, lang, variant, model) cell).
A bare language name (zehn) matches every variant of that language.

GATE: H5 point estimate is worse than rust_strict

## Stability

Variance of first_try_pass across repeats (population variance), averaged over tasks.

| lang | variant | model | tasks | stability | tasks with variance > 0 | repeats |
|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 6 | 0.000 | 0 | 1 |
| python_strict | default | gemini:gemma-4-31b-it | 6 | 0.000 | 0 | 1 |
| rust | default | gemini:gemma-4-31b-it | 6 | 0.000 | 0 | 1 |
| rust_strict | default | gemini:gemma-4-31b-it | 6 | 0.000 | 0 | 1 |
| ts_strict | default | gemini:gemma-4-31b-it | 6 | 0.000 | 0 | 1 |
| zehn | default | gemini:gemma-4-31b-it | 6 | 0.000 | 0 | 1 |

## Calibration

Unsolved = no run of any language has final_pass. Solved by all = every run of every language has final_pass.

Tasks no language solved (0): none

Tasks every language solved (5): domain_001, domain_005, edit_003, pure_002, text_001
