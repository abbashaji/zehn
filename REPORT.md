# Benchmark report

## Runs

| dir | run_id | set | records | tasks | meta |
|---|---|---|---|---|---|
| baseline-gemini-gemma-4-31b-it | baseline-gemini-gemma-4-31b-it | dev | 795 | 30 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '5', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'baseline-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330'], date_utc=2026-10-14T06:11:08Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=5, run_id=baseline-gemini-gemma-4-31b-it, seed=1234, sessions=[{'date_utc': '2026-10-12T20:42:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T05:09:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T13:25:10Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T19:29:28Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-14T01:02:51Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-14T06:11:08Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}], set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_002', 'domain_003', 'domain_004', 'domain_005', 'domain_006', 'edit_001', 'edit_002', 'edit_003', 'edit_004', 'edit_005', 'edit_006', 'effect_001', 'effect_002', 'effect_003', 'effect_004', 'effect_005', 'effect_006', 'pure_001', 'pure_002', 'pure_003', 'pure_004', 'pure_005', 'pure_006', 'text_001', 'text_002', 'text_003', 'text_004', 'text_005', 'text_006'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b-it | pilot-gemini-gemma-4-31b-it | dev | 36 | 6 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'pilot-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,domain_005,edit_003,effect_004,pure_002,text_001 '], date_utc=2026-10-12T18:34:01Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_005', 'edit_003', 'effect_004', 'pure_002', 'text_001'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b | - | - | 0 | 0 | api_hosts={'gemini:gemma-4-31b': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b', '--run-id', 'pilot-gemini-gemma-4-31b', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,edit_001,effect_001,pure_001,text_004,effect_004'], date_utc=2026-10-12T18:16:43Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'edit_001', 'effect_001', 'effect_004', 'pure_001', 'text_004'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |

## Runs left out (ended on an error)

These runs hit an error before they could finish (API outage, tool crash). They are counted in no metric below; `run.py run --resume` redoes the API ones.

| lang | valid runs | left out | kinds |
|---|---|---|---|
| python_plain | 139 | 17 | ModelError 500 |
| python_strict | 140 | 16 | ModelError 500, ModelError 503 |
| rust | 138 | 18 | ModelError 500 |
| rust_strict | 137 | 19 | ModelError 500 |
| ts_strict | 138 | 18 | ModelError 500 |
| zehn | 139 | 17 | ModelError 500 |

max_rounds used for censoring: 5
Bootstrap: 10000 resamples over tasks, seed 1234, 95% percentile interval.

## Results per language, variant and model

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 139 | 0.942 | 0.942 | 0.000 (censored 0/139) | 0.058 | n/a | 2483.0 | 0.008 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 140 | 0.950 | 0.950 | 0.021 (censored 0/140) | 0.050 | 0.000 | 3149.0 | 0.014 |
| rust | default | gemini:gemma-4-31b-it | 30 | 138 | 0.942 | 0.949 | 0.007 (censored 0/138) | 0.051 | 0.000 | 2275.7 | 0.012 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 137 | 0.956 | 0.956 | 0.095 (censored 0/137) | 0.044 | 0.000 | 3049.7 | 0.015 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 138 | 0.572 | 0.935 | 0.377 (censored 0/138) | 0.065 | 0.453 | 4261.7 | 0.147 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 139 | 0.568 | 0.935 | 1.007 (censored 5/139) | 0.029 | 0.002 | 22338.5 | 0.114 |

## Per category (models pooled)

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 6 | 29 | 1.000 | 1.000 | 0.000 |
| domain | python_strict | default | 6 | 29 | 1.000 | 1.000 | 0.000 |
| domain | rust | default | 6 | 29 | 0.966 | 1.000 | 0.000 |
| domain | rust_strict | default | 6 | 28 | 1.000 | 1.000 | 0.000 |
| domain | ts_strict | default | 6 | 29 | 0.621 | 1.000 | 0.000 |
| domain | zehn | default | 6 | 29 | 0.345 | 0.931 | 0.000 |
| edit | python_plain | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| edit | python_strict | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| edit | rust | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| edit | rust_strict | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| edit | ts_strict | default | 6 | 27 | 0.815 | 1.000 | 0.000 |
| edit | zehn | default | 6 | 27 | 0.926 | 1.000 | 0.000 |
| effect | python_plain | default | 6 | 28 | 0.714 | 0.714 | 0.286 |
| effect | python_strict | default | 6 | 28 | 0.750 | 0.750 | 0.250 |
| effect | rust | default | 6 | 28 | 0.750 | 0.750 | 0.250 |
| effect | rust_strict | default | 6 | 28 | 0.786 | 0.786 | 0.214 |
| effect | ts_strict | default | 6 | 28 | 0.321 | 0.679 | 0.321 |
| effect | zehn | default | 6 | 28 | 0.357 | 0.821 | 0.107 |
| pure | python_plain | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| pure | python_strict | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| pure | rust | default | 6 | 26 | 1.000 | 1.000 | 0.000 |
| pure | rust_strict | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| pure | ts_strict | default | 6 | 27 | 0.407 | 1.000 | 0.000 |
| pure | zehn | default | 6 | 27 | 0.667 | 0.963 | 0.000 |
| text | python_plain | default | 6 | 28 | 1.000 | 1.000 | 0.000 |
| text | python_strict | default | 6 | 29 | 1.000 | 1.000 | 0.000 |
| text | rust | default | 6 | 28 | 1.000 | 1.000 | 0.000 |
| text | rust_strict | default | 6 | 27 | 1.000 | 1.000 | 0.000 |
| text | ts_strict | default | 6 | 27 | 0.704 | 1.000 | 0.000 |
| text | zehn | default | 6 | 28 | 0.571 | 0.964 | 0.036 |

## Hypotheses H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.603 | [0.470, 0.735] | 30 | 4 | refuted (underpowered) |
| H2 | repair rounds, zehn - python_strict | 0.973 | [0.642, 1.323] | 30 | 4 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | -0.019 | [-0.059, 0.011] | 30 | 4 | inconclusive (underpowered) |
| H4 | total tokens, zehn - python_strict | 19052.118 | [14883.087, 23462.988] | 30 | 4 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | -0.021 | [-0.049, 0.006] | 30 | 4 | inconclusive (underpowered) |

Underpowered = fewer than 150 tasks or fewer than 5 repeats (smallest (task, lang, variant, model) cell).
A bare language name (zehn) matches every variant of that language.

GATE: H5 point estimate is worse than rust_strict

## Stability

Variance of first_try_pass across repeats (population variance), averaged over tasks.

| lang | variant | model | tasks | stability | tasks with variance > 0 | repeats |
|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 0.008 | 1 | 4 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 0.014 | 2 | 4 |
| rust | default | gemini:gemma-4-31b-it | 30 | 0.012 | 2 | 4 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 0.015 | 2 | 4 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 0.147 | 20 | 4 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 0.114 | 17 | 4 |

## Calibration

Unsolved = no run of any language has final_pass. Solved by all = every run of every language has final_pass.

Tasks no language solved (0): none

Tasks every language solved (25): domain_001, domain_002, domain_003, domain_005, domain_006, edit_001, edit_002, edit_003, edit_004, edit_005, edit_006, effect_001, effect_002, effect_003, effect_005, pure_001, pure_002, pure_003, pure_004, pure_006, text_002, text_003, text_004, text_005, text_006
