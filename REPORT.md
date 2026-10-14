# Benchmark report

## Runs

| dir | run_id | set | records | tasks | meta |
|---|---|---|---|---|---|
| baseline-gemini-gemma-4-31b-it | baseline-gemini-gemma-4-31b-it | dev | 899 | 30 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '5', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'baseline-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330'], date_utc=2026-10-14T16:23:49Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=5, run_id=baseline-gemini-gemma-4-31b-it, seed=1234, sessions=[{'date_utc': '2026-10-12T20:42:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T05:09:59Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T13:25:10Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-13T19:29:28Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-14T01:02:51Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-14T06:11:08Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-14T11:03:20Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}, {'date_utc': '2026-10-14T16:23:49Z', 'python': '3.12.15', 'tools': {'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}}], set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_002', 'domain_003', 'domain_004', 'domain_005', 'domain_006', 'edit_001', 'edit_002', 'edit_003', 'edit_004', 'edit_005', 'edit_006', 'effect_001', 'effect_002', 'effect_003', 'effect_004', 'effect_005', 'effect_006', 'pure_001', 'pure_002', 'pure_003', 'pure_004', 'pure_005', 'pure_006', 'text_001', 'text_002', 'text_003', 'text_004', 'text_005', 'text_006'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b-it | pilot-gemini-gemma-4-31b-it | dev | 36 | 6 | api_hosts={'gemini:gemma-4-31b-it': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b-it', '--run-id', 'pilot-gemini-gemma-4-31b-it', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,domain_005,edit_003,effect_004,pure_002,text_001 '], date_utc=2026-10-12T18:34:01Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b-it'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b-it, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'domain_005', 'edit_003', 'effect_004', 'pure_002', 'text_001'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |
| pilot-gemini-gemma-4-31b | - | - | 0 | 0 | api_hosts={'gemini:gemma-4-31b': 'generativelanguage.googleapis.com'}, argv=['run', '--lang', 'zehn,python_plain,python_strict,ts_strict,rust,rust_strict', '--repeats', '1', '--models', 'gemini:gemma-4-31b', '--run-id', 'pilot-gemini-gemma-4-31b', '--resume', '--yes', '--time-budget-minutes', '330', '--only', 'domain_001,edit_001,effect_001,pure_001,text_004,effect_004'], date_utc=2026-10-12T18:16:43Z, langs=['zehn', 'python_plain', 'python_strict', 'ts_strict', 'rust', 'rust_strict'], limits_per_key={'rpm': 30, 'tpm': 16000, 'rpd': 14400}, max_output_tokens=8192, max_rounds=5, models=['gemini:gemma-4-31b'], python=3.12.15, repeats=1, run_id=pilot-gemini-gemma-4-31b, seed=1234, set=dev, sources={'zehn.py': '0aa3eb68b92e2acd3aaa77399a70e1a569d238f44d0142ab582785d56bb16f73', 'zehnlib': {}}, tasks=['domain_001', 'edit_001', 'effect_001', 'effect_004', 'pure_001', 'text_004'], temperature=1.0, tools={'mypy': 'mypy 2.4.0 (compiled: yes)', 'ruff': 'ruff 0.17.0'}, variant=default |

## Runs left out (ended on an error)

These runs hit an error before they could finish (API outage, tool crash). They are counted in no metric below; `run.py run --resume` redoes the API ones.

| lang | valid runs | left out | kinds |
|---|---|---|---|
| python_plain | 156 | 0 | - |
| python_strict | 156 | 0 | - |
| rust | 155 | 1 | ModelError 500 |
| rust_strict | 156 | 0 | - |
| ts_strict | 156 | 0 | - |
| zehn | 156 | 0 | - |

max_rounds used for censoring: 5
Bootstrap: 10000 resamples over tasks, seed 1234, 95% percentile interval.

## Results per language, variant and model

| lang | variant | model | tasks | runs | pass@1 | pass_repair | repair rounds | silent-bug rate | hallucination rate | total tokens | stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 156 | 0.949 | 0.949 | 0.000 (censored 0/156) | 0.051 | n/a | 2490.4 | 0.008 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 156 | 0.955 | 0.955 | 0.019 (censored 0/156) | 0.045 | 0.000 | 3114.6 | 0.014 |
| rust | default | gemini:gemma-4-31b-it | 30 | 155 | 0.948 | 0.955 | 0.006 (censored 0/155) | 0.045 | 0.000 | 2248.1 | 0.011 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 156 | 0.962 | 0.962 | 0.096 (censored 0/156) | 0.038 | 0.000 | 3013.1 | 0.015 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 156 | 0.583 | 0.942 | 0.372 (censored 0/156) | 0.058 | 0.424 | 4251.8 | 0.143 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 156 | 0.577 | 0.942 | 0.981 (censored 5/156) | 0.026 | 0.002 | 22053.6 | 0.112 |

## Per category (models pooled)

| category | lang | variant | tasks | runs | pass@1 | pass_repair | silent-bug rate |
|---|---|---|---|---|---|---|---|
| domain | python_plain | default | 6 | 32 | 1.000 | 1.000 | 0.000 |
| domain | python_strict | default | 6 | 32 | 1.000 | 1.000 | 0.000 |
| domain | rust | default | 6 | 31 | 0.968 | 1.000 | 0.000 |
| domain | rust_strict | default | 6 | 32 | 1.000 | 1.000 | 0.000 |
| domain | ts_strict | default | 6 | 32 | 0.656 | 1.000 | 0.000 |
| domain | zehn | default | 6 | 32 | 0.344 | 0.938 | 0.000 |
| edit | python_plain | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| edit | python_strict | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| edit | rust | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| edit | rust_strict | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| edit | ts_strict | default | 6 | 31 | 0.839 | 1.000 | 0.000 |
| edit | zehn | default | 6 | 31 | 0.935 | 1.000 | 0.000 |
| effect | python_plain | default | 6 | 31 | 0.742 | 0.742 | 0.258 |
| effect | python_strict | default | 6 | 31 | 0.774 | 0.774 | 0.226 |
| effect | rust | default | 6 | 31 | 0.774 | 0.774 | 0.226 |
| effect | rust_strict | default | 6 | 31 | 0.806 | 0.806 | 0.194 |
| effect | ts_strict | default | 6 | 31 | 0.355 | 0.710 | 0.290 |
| effect | zehn | default | 6 | 31 | 0.387 | 0.839 | 0.097 |
| pure | python_plain | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| pure | python_strict | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| pure | rust | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| pure | rust_strict | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| pure | ts_strict | default | 6 | 31 | 0.419 | 1.000 | 0.000 |
| pure | zehn | default | 6 | 31 | 0.645 | 0.968 | 0.000 |
| text | python_plain | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| text | python_strict | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| text | rust | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| text | rust_strict | default | 6 | 31 | 1.000 | 1.000 | 0.000 |
| text | ts_strict | default | 6 | 31 | 0.645 | 1.000 | 0.000 |
| text | zehn | default | 6 | 31 | 0.581 | 0.968 | 0.032 |

## Hypotheses H1 to H5

| H | comparison | estimate | 95% CI | tasks | repeats | verdict |
|---|---|---|---|---|---|---|
| H1 | pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8) | 0.601 | [0.469, 0.733] | 30 | 5 | refuted (underpowered) |
| H2 | repair rounds, zehn - python_strict | 0.969 | [0.640, 1.313] | 30 | 5 | refuted (underpowered) |
| H3 | silent-bug rate, zehn - python_strict | -0.019 | [-0.059, 0.011] | 30 | 5 | inconclusive (underpowered) |
| H4 | total tokens, zehn - python_strict | 19048.354 | [14964.027, 23338.283] | 30 | 5 | refuted (underpowered) |
| H5 | pass_repair, zehn - rust_strict | -0.019 | [-0.046, 0.006] | 30 | 5 | inconclusive (underpowered) |

Underpowered = fewer than 150 tasks or fewer than 5 repeats (smallest (task, lang, variant, model) cell).
A bare language name (zehn) matches every variant of that language.

GATE: H5 point estimate is worse than rust_strict

## Stability

Variance of first_try_pass across repeats (population variance), averaged over tasks.

| lang | variant | model | tasks | stability | tasks with variance > 0 | repeats |
|---|---|---|---|---|---|---|
| python_plain | default | gemini:gemma-4-31b-it | 30 | 0.008 | 1 | 5 |
| python_strict | default | gemini:gemma-4-31b-it | 30 | 0.014 | 2 | 5 |
| rust | default | gemini:gemma-4-31b-it | 30 | 0.011 | 2 | 4 |
| rust_strict | default | gemini:gemma-4-31b-it | 30 | 0.015 | 2 | 5 |
| ts_strict | default | gemini:gemma-4-31b-it | 30 | 0.143 | 20 | 5 |
| zehn | default | gemini:gemma-4-31b-it | 30 | 0.112 | 17 | 5 |

## Calibration

Unsolved = no run of any language has final_pass. Solved by all = every run of every language has final_pass.

Tasks no language solved (0): none

Tasks every language solved (25): domain_001, domain_002, domain_003, domain_005, domain_006, edit_001, edit_002, edit_003, edit_004, edit_005, edit_006, effect_001, effect_002, effect_003, effect_005, pure_001, pure_002, pure_003, pure_004, pure_006, text_002, text_003, text_004, text_005, text_006
