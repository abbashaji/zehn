# Benchmark report

## Runs

| dir | run_id | set | records | tasks | meta |
|---|---|---|---|---|---|
| baseline-gemini-gemma-4-31b-it | baseline-gemini-gemma-4-31b-it | dev | 615 | 30 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '5', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'baseline-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330'], date_utc=2026-10-13T19:29:28Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=5, run_id=baseline-gemini-gemma-4-31b-it, seed=1234, sessions=[{'date_utc': '2026-10-12T20:42:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T05:09:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T13:25:10Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T19:29:28Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}], set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_002', 'domain_003', 'domain_004', 'domain_005', 'domain_006', 'edit_001', 'edit_002', 'edit_003', 'edit_004', 'edit_005', 'edit_006', 'effect_001', 'effect_002', 'effect_003', 'effect_004', 'effect_005', 'effect_006', 'pure_001', 'pure_002', 'pure_003', 'pure_004', 'pure_005', 'pure_006', 'text_001', 'text_002', 'text_003', 'text_004', 'text_005', 'text_006'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b-it | pilot-gemini-gemma-4-31b-it | dev | 36 | 6 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'pilot-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,domain_005,edit_003,effect_004,pure_002,text_001 '], date_utc=2026-10-12T18:34:01Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_005', 'edit_003', 'effect_004', 'pure_002', 'text_001'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b | - | - | 0 | 0 | api_hosts={'gemini:gemma-4-31b': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b', '--run-id', 'pilot-gemini-gemma-4-31b', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,edit_001,effect_001,pure_001,text_004,effect_004'], date_utc=2026-10-12T18:16:43Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'edit_001', 'effect_001', 'effect_004', 'pure_001', 'text_004'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |

## Runs left out (ended on an error)

These runs hit an error before they could finish (API outage, tool crash). They are counted in no metric below; `run.py run --resume` redoes the API ones.

| lang | valid runs | left out | kinds |
|---|---|---|---|
| python_plain | 112 | 19 | ModelError 500, ModelError 503 |
| python_strict | 115 | 17 | ModelError 500, ModelError 503 |
| rust | 106 | 25 | ModelError 500, ModelError 503 |
| rust_strict | 113 | 19 | ModelError 500, ModelError 503 |
| ts_strict | 108 | 24 | ModelError 500, ModelError 503 |
| zehn | 97 | 34 | ModelError 500, ModelError 503 |

max_rounds used for censoring: 5
Bootstrap: 10000 resamples over tasks, seed 1234, 95% percentile interval.

## Results per language, variant and model

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 112 | 0.946 | 0.946 | 0.000 (censored 0/112) | 0.054 | n/a | 2398.6 | 0.006 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 115 | 0.948 | 0.948 | 0.026 (censored 0/115) | 0.052 | 0.000 | 3088.7 | 0.013 |
| rust | default | gemini:gemma-4-31b-it | 30 | 106 | 0.953 | 0.962 | 0.009 (censored 0/106) | 0.038 | 0.000 | 2284.2 | 0.013 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 113 | 0.965 | 0.965 | 0.115 (censored 0/113) | 0.035 | 0.000 | 3101.4 | 0.013 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 108 | 0.574 | 0.944 | 0.380 (censored 0/108) | 0.056 | 0.453 | 4213.2 | 0.131 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 97 | 0.598 | 0.959 | 0.876 (censored 3/97) | 0.010 | 0.004 | 20441.1 | 0.093 |

## Per category (models pooled)

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 6 | 22 | 1.000 | 1.000 | 0.000 |
| domain | python_strict | default | 6 | 23 | 1.000 | 1.000 | 0.000 |
| domain | rust | default | 6 | 22 | 0.955 | 1.000 | 0.000 |
| domain | rust_strict | default | 6 | 23 | 1.000 | 1.000 | 0.000 |
| domain | ts_strict | default | 6 | 21 | 0.571 | 1.000 | 0.000 |
| domain | zehn | default | 6 | 22 | 0.364 | 0.955 | 0.000 |
| edit | python_plain | default | 6 | 20 | 1.000 | 1.000 | 0.000 |
| edit | python_strict | default | 6 | 23 | 1.000 | 1.000 | 0.000 |
| edit | rust | default | 6 | 22 | 1.000 | 1.000 | 0.000 |
| edit | rust_strict | default | 6 | 25 | 1.000 | 1.000 | 0.000 |
| edit | ts_strict | default | 6 | 24 | 0.833 | 1.000 | 0.000 |
| edit | zehn | default | 6 | 21 | 0.905 | 1.000 | 0.000 |
| effect | python_plain | default | 6 | 23 | 0.739 | 0.739 | 0.261 |
| effect | python_strict | default | 6 | 24 | 0.750 | 0.750 | 0.250 |
| effect | rust | default | 6 | 20 | 0.800 | 0.800 | 0.200 |
| effect | rust_strict | default | 6 | 21 | 0.810 | 0.810 | 0.190 |
| effect | ts_strict | default | 6 | 21 | 0.286 | 0.714 | 0.286 |
| effect | zehn | default | 6 | 16 | 0.188 | 0.812 | 0.062 |
| pure | python_plain | default | 6 | 24 | 1.000 | 1.000 | 0.000 |
| pure | python_strict | default | 6 | 22 | 1.000 | 1.000 | 0.000 |
| pure | rust | default | 6 | 21 | 1.000 | 1.000 | 0.000 |
| pure | rust_strict | default | 6 | 24 | 1.000 | 1.000 | 0.000 |
| pure | ts_strict | default | 6 | 20 | 0.400 | 1.000 | 0.000 |
| pure | zehn | default | 6 | 19 | 0.789 | 1.000 | 0.000 |
| text | python_plain | default | 6 | 23 | 1.000 | 1.000 | 0.000 |
| text | python_strict | default | 6 | 23 | 1.000 | 1.000 | 0.000 |
| text | rust | default | 6 | 21 | 1.000 | 1.000 | 0.000 |
| text | rust_strict | default | 6 | 20 | 1.000 | 1.000 | 0.000 |
| text | ts_strict | default | 6 | 22 | 0.727 | 1.000 | 0.000 |
| text | zehn | default | 6 | 19 | 0.684 | 1.000 | 0.000 |

## Hypotheses H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.570 | [0.429, 0.713] | 30 | 1 | refuted (underpowered) |
| H2 | repair rounds, zehn - python_strict | 1.034 | [0.638, 1.466] | 30 | 1 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | -0.023 | [-0.060, 0.000] | 30 | 1 | inconclusive (underpowered) |
| H4 | total tokens, zehn - python_strict | 19891.073 | [14854.772, 25442.586] | 30 | 1 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | -0.025 | [-0.050, 0.000] | 30 | 1 | refuted (underpowered) |

Underpowered = fewer than 150 tasks or fewer than 5 repeats (smallest (task, lang, variant, model) cell).
A bare language name (zehn) matches every variant of that language.

GATE: H5 point estimate is worse than rust_strict

## Stability

Variance of first_try_pass across repeats (population variance), averaged over tasks.

| lang | variant | model | tasks | stability | tasks with variance > 0 | repeats |
|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 0.006 | 1 | 2 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 0.013 | 2 | 2 |
| rust | default | gemini:gemma-4-31b-it | 30 | 0.013 | 2 | 2 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 0.013 | 2 | 3 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 0.131 | 17 | 2 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 0.093 | 13 | 1 |

## Calibration

Unsolved = no run of any language has final_pass. Solved by all = every run of every language has final_pass.

Tasks no language solved (0): none

Tasks every language solved (28): domain_001, domain_002, domain_003, domain_004, domain_005, domain_006, edit_001, edit_002, edit_003, edit_004, edit_005, edit_006, effect_001, effect_002, effect_003, effect_005, pure_001, pure_002, pure_003, pure_004, pure_005, pure_006, text_001, text_002, text_003, text_004, text_005, text_006
