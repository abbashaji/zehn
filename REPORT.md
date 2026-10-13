# Benchmark report

## Runs

| dir | run_id | set | records | tasks | meta |
|---|---|---|---|---|---|
| baseline-gemini-gemma-4-31b-it | baseline-gemini-gemma-4-31b-it | dev | 447 | 30 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '5', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'baseline-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330'], date_utc=2026-10-13T05:09:59Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=5, run_id=baseline-gemini-gemma-4-31b-it, seed=1234, sessions=[{'date_utc': '2026-10-12T20:42:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T05:09:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}], set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_002', 'domain_003', 'domain_004', 'domain_005', 'domain_006', 'edit_001', 'edit_002', 'edit_003', 'edit_004', 'edit_005', 'edit_006', 'effect_001', 'effect_002', 'effect_003', 'effect_004', 'effect_005', 'effect_006', 'pure_001', 'pure_002', 'pure_003', 'pure_004', 'pure_005', 'pure_006', 'text_001', 'text_002', 'text_003', 'text_004', 'text_005', 'text_006'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b-it | pilot-gemini-gemma-4-31b-it | dev | 36 | 6 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'pilot-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,domain_005,edit_003,effect_004,pure_002,text_001 '], date_utc=2026-10-12T18:34:01Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_005', 'edit_003', 'effect_004', 'pure_002', 'text_001'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b | - | - | 0 | 0 | api_hosts={'gemini:gemma-4-31b': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b', '--run-id', 'pilot-gemini-gemma-4-31b', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,edit_001,effect_001,pure_001,text_004,effect_004'], date_utc=2026-10-12T18:16:43Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'edit_001', 'effect_001', 'effect_004', 'pure_001', 'text_004'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |

max_rounds used for censoring: 5
Bootstrap: 10000 resamples over tasks, seed 1234, 95% percentile interval.

## Results per language, variant and model

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 81 | 0.864 | 0.864 | 0.395 (censored 8/81) | 0.037 | n/a | 2134.7 | 0.051 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 80 | 0.887 | 0.887 | 0.388 (censored 7/80) | 0.025 | 0.000 | 2849.3 | 0.053 |
| rust | default | gemini:gemma-4-31b-it | 30 | 81 | 0.815 | 0.827 | 0.556 (censored 11/81) | 0.037 | 0.000 | 1939.4 | 0.075 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 80 | 0.875 | 0.863 | 0.487 (censored 8/80) | 0.037 | 0.000 | 2617.1 | 0.059 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 81 | 0.457 | 0.790 | 0.938 (censored 12/81) | 0.062 | 0.424 | 3750.6 | 0.132 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 80 | 0.475 | 0.762 | 1.538 (censored 19/80) | 0.000 | 0.000 | 17530.2 | 0.132 |

## Per category (models pooled)

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 6 | 17 | 0.765 | 0.765 | 0.000 |
| domain | python_strict | default | 6 | 17 | 0.824 | 0.824 | 0.000 |
| domain | rust | default | 6 | 17 | 0.824 | 0.882 | 0.000 |
| domain | rust_strict | default | 6 | 17 | 0.941 | 0.941 | 0.000 |
| domain | ts_strict | default | 6 | 17 | 0.412 | 0.824 | 0.000 |
| domain | zehn | default | 6 | 17 | 0.353 | 0.882 | 0.000 |
| edit | python_plain | default | 6 | 16 | 0.875 | 0.875 | 0.000 |
| edit | python_strict | default | 6 | 16 | 1.000 | 1.000 | 0.000 |
| edit | rust | default | 6 | 16 | 0.875 | 0.875 | 0.000 |
| edit | rust_strict | default | 6 | 16 | 1.000 | 0.938 | 0.000 |
| edit | ts_strict | default | 6 | 16 | 0.812 | 0.938 | 0.000 |
| edit | zehn | default | 6 | 16 | 0.625 | 0.750 | 0.000 |
| effect | python_plain | default | 6 | 16 | 0.750 | 0.750 | 0.188 |
| effect | python_strict | default | 6 | 15 | 0.733 | 0.733 | 0.133 |
| effect | rust | default | 6 | 16 | 0.625 | 0.625 | 0.188 |
| effect | rust_strict | default | 6 | 15 | 0.667 | 0.667 | 0.200 |
| effect | ts_strict | default | 6 | 16 | 0.188 | 0.500 | 0.312 |
| effect | zehn | default | 6 | 15 | 0.200 | 0.533 | 0.000 |
| pure | python_plain | default | 6 | 16 | 0.938 | 0.938 | 0.000 |
| pure | python_strict | default | 6 | 16 | 0.938 | 0.938 | 0.000 |
| pure | rust | default | 6 | 16 | 0.875 | 0.875 | 0.000 |
| pure | rust_strict | default | 6 | 16 | 0.875 | 0.875 | 0.000 |
| pure | ts_strict | default | 6 | 16 | 0.188 | 0.812 | 0.000 |
| pure | zehn | default | 6 | 16 | 0.625 | 0.875 | 0.000 |
| text | python_plain | default | 6 | 16 | 1.000 | 1.000 | 0.000 |
| text | python_strict | default | 6 | 16 | 0.938 | 0.938 | 0.000 |
| text | rust | default | 6 | 16 | 0.875 | 0.875 | 0.000 |
| text | rust_strict | default | 6 | 16 | 0.875 | 0.875 | 0.000 |
| text | ts_strict | default | 6 | 16 | 0.688 | 0.875 | 0.000 |
| text | zehn | default | 6 | 16 | 0.562 | 0.750 | 0.000 |

## Hypotheses H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.503 | [0.371, 0.640] | 30 | 2 | refuted (underpowered) |
| H2 | repair rounds, zehn - python_strict | 1.203 | [0.764, 1.650] | 30 | 2 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | -0.022 | [-0.067, 0.000] | 30 | 2 | inconclusive (underpowered) |
| H4 | total tokens, zehn - python_strict | 15271.631 | [12039.742, 18631.317] | 30 | 2 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | -0.100 | [-0.181, -0.022] | 30 | 2 | refuted (underpowered) |

Underpowered = fewer than 150 tasks or fewer than 5 repeats (smallest (task, lang, variant, model) cell).
A bare language name (zehn) matches every variant of that language.

GATE: H5 point estimate is worse than rust_strict

## Stability

Variance of first_try_pass across repeats (population variance), averaged over tasks.

| lang | variant | model | tasks | stability | tasks with variance > 0 | repeats |
|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 0.051 | 7 | 2 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 0.053 | 7 | 2 |
| rust | default | gemini:gemma-4-31b-it | 30 | 0.075 | 10 | 2 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 0.059 | 8 | 2 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 0.132 | 17 | 2 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 0.132 | 17 | 2 |

## Calibration

Unsolved = no run of any language has final_pass. Solved by all = every run of every language has final_pass.

Tasks no language solved (0): none

Tasks every language solved (6): domain_003, domain_006, edit_006, pure_003, text_004, text_006
