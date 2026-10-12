# ADR-0014 The zehn benchmark adapter forgives layout-only errors
Status: unmeasured

## Problem
The pilot (gemma-4-31b-it, 6 tasks) showed 9 of 13 failed zehn tool rounds had E0203 (non-canonical layout under `--strict`) as the only error. The model cannot run `zehn fmt`, so two runs (effect_004, domain_005) spent their last three rounds on E0203 alone while their final programs passed every hidden test. The benchmark was measuring whitespace, not Zehn.

## Options
1. Leave it (the language demands canonical text from its author).
2. Adapter canonicalizes with `zehn fmt` when E0203 is the only error, and hides E0203 from feedback when real errors remain (chosen).
3. Return the canonical text inside the E0203 feedback.

## Experiment run (or why none)
None yet. The pilot is the motivation, not a test of the fix. Rerun the pilot tasks to measure the effect.

## Numeric result
None.

## Decision
Option 2, in `bench/benchlib/adapters/zehn.py` (`tool_check`). A layout-only candidate is accepted after `zehn fmt` plus a clean re-check; the accepted round records one `W0301` diagnostic so the rate stays visible. When other errors remain, E0203 is dropped from the feedback so line numbers match the model's own text. Hidden tests still run on the model's raw text (layout never changes meaning). The language and `zehn check` are unchanged. Covered by two tests in `bench/tests/test_core_adapters.py`.

## Revisit condition
Report formatting-failure rates separately if layout skill matters for the language's claims; if `fmt` ever changes meaning, drop this. Other languages' strict tools (ruff, rustfmt, tsc) were not reviewed for the same asymmetry.
