# ADR-0015 API failures are redone and left out of reports; rounds record diagnostic messages
Status: unmeasured

## Problem
The first full baseline (gemma-4-31b-it) lost 154 of 642 runs to Gemini HTTP 500/503/429 after 6 retries. Such a run is recorded with `error` set and no attempt, `--resume` treats it as done, and the report counted it as a failed run: every language fell from about 0.96 to about 0.78 pass_repair and H5 turned into a false "zehn worse than rust_strict" gate. Records also kept only diagnostic codes, so the cause of zehn's E0201 and E0602 failures could not be read.

## Options
1. Keep as is and filter by hand.
2. `--resume` moves API-failure records aside and redoes them; the report leaves every errored run out of the metrics and lists it in its own section; rounds gain an optional `diags` list (chosen).
3. Count API failures as censored runs (rejected: they say nothing about the model).

## Experiment run (or why none)
None. Checked on the real 642-record file: 154 records moved, 488 kept, H5 moved from -0.100 [-0.197, -0.026] (counting outages) to +0.006 [-0.033, 0.050].

## Numeric result
See above (one snapshot, one model).

## Decision
Option 2. Retryable = error text `ModelError: giving up after N attempts (HTTP 429|5xx`; other errors (HTTP 4xx, tool crashes) are never retried automatically, but are also left out of the metrics and listed. Moved records go to `records.errors.jsonl` beside `records.jsonl` (nothing is deleted). `status` counts them as remaining; `run.py prune-errors --run-id X` does the move by hand. Round key `diags` is optional ([{code, line, message<=300 chars}], at most 8 per round), so schema 1 and old records stay valid.

## Revisit condition
If a model's API fails persistently, `--resume` retries forever (each workflow run once); add a retry cap per task then. A report that hides errors can mask a broken adapter: read the "Runs left out" table before trusting a result.
