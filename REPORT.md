# Benchmark report

## Runs

| dir | run_id | set | records | tasks | meta |
|---|---|---|---|---|---|
| baseline-gemini-gemma-4-31b-it | baseline-gemini-gemma-4-31b-it | dev | 241 | 30 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '5', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'baseline-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330'], date_utc=2026-10-12T20:42:59Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=5, run_id=baseline-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_002', 'domain_003', 'domain_004', 'domain_005', 'domain_006', 'edit_001', 'edit_002', 'edit_003', 'edit_004', 'edit_005', 'edit_006', 'effect_001', 'effect_002', 'effect_003', 'effect_004', 'effect_005', 'effect_006', 'pure_001', 'pure_002', 'pure_003', 'pure_004', 'pure_005', 'pure_006', 'text_001', 'text_002', 'text_003', 'text_004', 'text_005', 'text_006'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b-it | pilot-gemini-gemma-4-31b-it | dev | 36 | 6 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'pilot-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,domain_005,edit_003,effect_004,pure_002,text_001 '], date_utc=2026-10-12T18:34:01Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_005', 'edit_003', 'effect_004', 'pure_002', 'text_001'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b | - | - | 0 | 0 | api_hosts={'gemini:gemma-4-31b': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b', '--run-id', 'pilot-gemini-gemma-4-31b', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,edit_001,effect_001,pure_001,text_004,effect_004'], date_utc=2026-10-12T18:16:43Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'edit_001', 'effect_001', 'effect_004', 'pure_001', 'text_004'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |

max_rounds used for censoring: 5
Bootstrap: 10000 resamples over tasks, seed 1234, 95% percentile interval.

## Results per language, variant and model

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 46 | 0.957 | 0.957 | 0.087 (censored 1/46) | 0.022 | n/a | 2468.5 | 0.008 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 46 | 0.957 | 0.957 | 0.130 (censored 1/46) | 0.022 | 0.000 | 3141.3 | 0.008 |
| rust | default | gemini:gemma-4-31b-it | 30 | 46 | 0.913 | 0.935 | 0.109 (censored 1/46) | 0.043 | 0.000 | 2275.7 | 0.008 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 47 | 0.957 | 0.957 | 0.064 (censored 0/47) | 0.043 | 0.000 | 2872.7 | 0.008 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 46 | 0.500 | 0.957 | 0.478 (censored 0/46) | 0.043 | 0.500 | 4452.3 | 0.050 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 46 | 0.565 | 0.935 | 1.130 (censored 3/46) | 0.000 | 0.000 | 23456.1 | 0.042 |

## Per category (models pooled)

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 6 | 10 | 0.900 | 0.900 | 0.000 |
| domain | python_strict | default | 6 | 10 | 1.000 | 1.000 | 0.000 |
| domain | rust | default | 6 | 10 | 0.900 | 1.000 | 0.000 |
| domain | rust_strict | default | 6 | 11 | 1.000 | 1.000 | 0.000 |
| domain | ts_strict | default | 6 | 10 | 0.600 | 1.000 | 0.000 |
| domain | zehn | default | 6 | 10 | 0.400 | 0.900 | 0.000 |
| edit | python_plain | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| edit | python_strict | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| edit | rust | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| edit | rust_strict | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| edit | ts_strict | default | 6 | 9 | 0.778 | 1.000 | 0.000 |
| edit | zehn | default | 6 | 9 | 0.778 | 1.000 | 0.000 |
| effect | python_plain | default | 6 | 9 | 0.889 | 0.889 | 0.111 |
| effect | python_strict | default | 6 | 9 | 0.778 | 0.778 | 0.111 |
| effect | rust | default | 6 | 9 | 0.778 | 0.778 | 0.222 |
| effect | rust_strict | default | 6 | 9 | 0.778 | 0.778 | 0.222 |
| effect | ts_strict | default | 6 | 9 | 0.222 | 0.778 | 0.222 |
| effect | zehn | default | 6 | 9 | 0.222 | 0.778 | 0.000 |
| pure | python_plain | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| pure | python_strict | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| pure | rust | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| pure | rust_strict | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| pure | ts_strict | default | 6 | 9 | 0.222 | 1.000 | 0.000 |
| pure | zehn | default | 6 | 9 | 0.667 | 1.000 | 0.000 |
| text | python_plain | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| text | python_strict | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| text | rust | default | 6 | 9 | 0.889 | 0.889 | 0.000 |
| text | rust_strict | default | 6 | 9 | 1.000 | 1.000 | 0.000 |
| text | ts_strict | default | 6 | 9 | 0.667 | 1.000 | 0.000 |
| text | zehn | default | 6 | 9 | 0.778 | 1.000 | 0.000 |

## Hypotheses H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.544 | [0.379, 0.709] | 30 | 1 | refuted (underpowered) |
| H2 | repair rounds, zehn - python_strict | 1.100 | [0.683, 1.550] | 30 | 1 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | -0.033 | [-0.100, 0.000] | 30 | 1 | inconclusive (underpowered) |
| H4 | total tokens, zehn - python_strict | 21310.100 | [16078.017, 27042.717] | 30 | 1 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | 0.000 | [-0.067, 0.083] | 30 | 1 | inconclusive (underpowered) |

Underpowered = fewer than 150 tasks or fewer than 5 repeats (smallest (task, lang, variant, model) cell).
A bare language name (zehn) matches every variant of that language.

## Stability

Variance of first_try_pass across repeats (population variance), averaged over tasks.

| lang | variant | model | tasks | stability | tasks with variance > 0 | repeats |
|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 0.008 | 1 | 1 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 0.008 | 1 | 1 |
| rust | default | gemini:gemma-4-31b-it | 30 | 0.008 | 1 | 1 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 0.008 | 1 | 1 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 0.050 | 6 | 1 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 0.042 | 5 | 1 |

## Calibration

Unsolved = no run of any language has final_pass. Solved by all = every run of every language has final_pass.

Tasks no language solved (0): none

Tasks every language solved (25): domain_001, domain_002, domain_003, domain_004, domain_006, edit_001, edit_002, edit_003, edit_004, edit_005, edit_006, effect_001, effect_002, effect_005, pure_001, pure_002, pure_003, pure_004, pure_005, pure_006, text_001, text_002, text_003, text_004, text_006
