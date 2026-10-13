# Benchmark report

## Runs

| dir | run_id | set | records | tasks | meta |
|---|---|---|---|---|---|
| baseline-gemini-gemma-4-31b-it | baseline-gemini-gemma-4-31b-it | dev | 642 | 30 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '5', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'baseline-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330'], date_utc=2026-10-13T13:25:10Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=5, run_id=baseline-gemini-gemma-4-31b-it, seed=1234, sessions=[{'date_utc': '2026-10-12T20:42:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T05:09:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T13:25:10Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}], set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_002', 'domain_003', 'domain_004', 'domain_005', 'domain_006', 'edit_001', 'edit_002', 'edit_003', 'edit_004', 'edit_005', 'edit_006', 'effect_001', 'effect_002', 'effect_003', 'effect_004', 'effect_005', 'effect_006', 'pure_001', 'pure_002', 'pure_003', 'pure_004', 'pure_005', 'pure_006', 'text_001', 'text_002', 'text_003', 'text_004', 'text_005', 'text_006'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b-it | pilot-gemini-gemma-4-31b-it | dev | 36 | 6 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'pilot-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,domain_005,edit_003,effect_004,pure_002,text_001 '], date_utc=2026-10-12T18:34:01Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_005', 'edit_003', 'effect_004', 'pure_002', 'text_001'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b | - | - | 0 | 0 | api_hosts={'gemini:gemma-4-31b': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b', '--run-id', 'pilot-gemini-gemma-4-31b', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,edit_001,effect_001,pure_001,text_004,effect_004'], date_utc=2026-10-12T18:16:43Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'edit_001', 'effect_001', 'effect_004', 'pure_001', 'text_004'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |

max_rounds used for censoring: 5
Bootstrap: 10000 resamples over tasks, seed 1234, 95% percentile interval.

## Results per language, variant and model

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 113 | 0.779 | 0.779 | 0.779 (censored 22/113) | 0.027 | n/a | 1963.6 | 0.115 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 113 | 0.788 | 0.788 | 0.770 (censored 21/113) | 0.027 | 0.000 | 2577.5 | 0.126 |
| rust | default | gemini:gemma-4-31b-it | 30 | 113 | 0.726 | 0.735 | 0.965 (censored 27/113) | 0.027 | 0.000 | 1732.5 | 0.139 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 113 | 0.796 | 0.779 | 0.841 (censored 21/113) | 0.035 | 0.000 | 2543.1 | 0.114 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 113 | 0.407 | 0.708 | 1.301 (censored 28/113) | 0.044 | 0.397 | 3446.8 | 0.145 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 113 | 0.416 | 0.664 | 1.894 (censored 38/113) | 0.000 | 0.000 | 15990.7 | 0.144 |

## Per category (models pooled)

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 6 | 24 | 0.708 | 0.708 | 0.000 |
| domain | python_strict | default | 6 | 24 | 0.750 | 0.750 | 0.000 |
| domain | rust | default | 6 | 24 | 0.708 | 0.750 | 0.000 |
| domain | rust_strict | default | 6 | 24 | 0.792 | 0.792 | 0.000 |
| domain | ts_strict | default | 6 | 24 | 0.333 | 0.667 | 0.000 |
| domain | zehn | default | 6 | 24 | 0.292 | 0.750 | 0.000 |
| edit | python_plain | default | 6 | 23 | 0.739 | 0.739 | 0.000 |
| edit | python_strict | default | 6 | 23 | 0.870 | 0.870 | 0.000 |
| edit | rust | default | 6 | 23 | 0.783 | 0.783 | 0.000 |
| edit | rust_strict | default | 6 | 23 | 0.913 | 0.870 | 0.000 |
| edit | ts_strict | default | 6 | 23 | 0.739 | 0.870 | 0.000 |
| edit | zehn | default | 6 | 23 | 0.609 | 0.696 | 0.000 |
| effect | python_plain | default | 6 | 22 | 0.682 | 0.682 | 0.136 |
| effect | python_strict | default | 6 | 22 | 0.682 | 0.682 | 0.136 |
| effect | rust | default | 6 | 22 | 0.545 | 0.545 | 0.136 |
| effect | rust_strict | default | 6 | 22 | 0.591 | 0.591 | 0.182 |
| effect | ts_strict | default | 6 | 22 | 0.136 | 0.500 | 0.227 |
| effect | zehn | default | 6 | 22 | 0.182 | 0.500 | 0.000 |
| pure | python_plain | default | 6 | 22 | 0.909 | 0.909 | 0.000 |
| pure | python_strict | default | 6 | 22 | 0.818 | 0.818 | 0.000 |
| pure | rust | default | 6 | 22 | 0.818 | 0.818 | 0.000 |
| pure | rust_strict | default | 6 | 22 | 0.864 | 0.864 | 0.000 |
| pure | ts_strict | default | 6 | 22 | 0.273 | 0.727 | 0.000 |
| pure | zehn | default | 6 | 22 | 0.500 | 0.682 | 0.000 |
| text | python_plain | default | 6 | 22 | 0.864 | 0.864 | 0.000 |
| text | python_strict | default | 6 | 22 | 0.818 | 0.818 | 0.000 |
| text | rust | default | 6 | 22 | 0.773 | 0.773 | 0.000 |
| text | rust_strict | default | 6 | 22 | 0.818 | 0.773 | 0.000 |
| text | ts_strict | default | 6 | 22 | 0.545 | 0.773 | 0.000 |
| text | zehn | default | 6 | 22 | 0.500 | 0.682 | 0.000 |

## Hypotheses H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.519 | [0.380, 0.667] | 30 | 3 | refuted (underpowered) |
| H2 | repair rounds, zehn - python_strict | 1.108 | [0.681, 1.538] | 30 | 3 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | -0.029 | [-0.080, 0.000] | 30 | 3 | inconclusive (underpowered) |
| H4 | total tokens, zehn - python_strict | 13711.501 | [10868.949, 16625.157] | 30 | 3 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | -0.110 | [-0.197, -0.026] | 30 | 3 | refuted (underpowered) |

Underpowered = fewer than 150 tasks or fewer than 5 repeats (smallest (task, lang, variant, model) cell).
A bare language name (zehn) matches every variant of that language.

GATE: H5 point estimate is worse than rust_strict

## Stability

Variance of first_try_pass across repeats (population variance), averaged over tasks.

| lang | variant | model | tasks | stability | tasks with variance > 0 | repeats |
|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 0.115 | 17 | 3 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 0.126 | 19 | 3 |
| rust | default | gemini:gemma-4-31b-it | 30 | 0.139 | 19 | 3 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 0.114 | 17 | 3 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 0.145 | 21 | 3 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 0.144 | 21 | 3 |

## Calibration

Unsolved = no run of any language has final_pass. Solved by all = every run of every language has final_pass.

Tasks no language solved (0): none

Tasks every language solved (1): domain_003
