# ADR-0018 Diagnostics are a versioned contract: `"schema": 1` in the envelope
Status: unmeasured

## Problem
Roadmap section 5 items 5 and 6: models and tools read `zehn check --json`, so its shape must be stable and documented, every error and warning code needs a worked example, and a change must be detectable by a consumer. Before this task `check --json` printed `{ok, diagnostics, definitions, examples}` with no version, `E0001` had no explain text, and no code had a tested broken/fixed pair.

## Options
1. Put the version in the envelope: one `"schema": 1` key, first in the object.
2. Put the version in every diagnostic object.
3. No version; rely on additive changes and on the docs.

## Experiment run (or why none)
None. No model has read the new output; the choice is about compatibility mechanics, not about model accuracy.

## Numeric result
None.

## Decision
Option 1. A consumer reads the version once, before looking at anything else; diagnostics are also printed outside the envelope (`run`, `patch`, usage errors) where a per-diagnostic version would repeat on every line for no reader's benefit. Rule written in `docs/DIAGNOSTICS.md`: within schema 1 keys are only ever added; removing, renaming or retyping a key means schema 2. The JSON Schema (draft-07, `docs/diagnostics.schema.json`) allows additional properties everywhere so that adding keys is legal; a test validates every diagnostic the catalog produces and every `check --json` envelope with a small hand-written validator (no `jsonschema` dependency).

Catalog: one `catalog/<CODE>/` per registered code (38: the 37 explain texts of v0.3 plus `E0001`, whose text is new). A completeness test iterates `zehnlib.errors.EXPLAIN`, so a later branch that registers a code and adds its folder needs no test edit.

Findings that shaped the catalog (all verified by running the program):
- `E0503` and `E0603` cannot be triggered by any program through `check` or `run`: `E0310` and `E0601` reject the program first. The plan named `E0503` alone as unreachable; `E0603` is the same kind of guard. Both entries carry `"unreachable": reason`, and the test proves the guard by calling `Interp` on the program without the static passes (`"probe"` names the call for `E0603`).
- `E0504` and `E0506` cannot be triggered by an example (the static passes catch every such program) but they can by `zehn run` with JSON arguments of the wrong shape; their entries use `"cli"`. `E0604` needs a `run` without `--grant`; it uses `"cli"` too.
- Two meta keys beyond the plan's format: `cli_fixed` (the corrected command for entries with `cli`) and `probe` (how to call an unreachable guard).
- `E0204` needs between 30 000 and 60 000 nested parentheses to trigger under `zehn check` at the default `--max-depth` (the CLI raises the host recursion limit with it); the catalog file nests 3 000, which trips `analyze` and `check --max-depth 100`. The meta note and a test say so.
- `W0201` needs a `.lock` file next to the program, so its folder holds `broken.zehn.lock` and `fixed.zehn.lock` (written by `zehn lock` on the version before the change).
- `tests/test_registry.py` asserted `len(EXPLAIN) == 37 + 1`; registering `E0001` (required for the registry and the catalog to agree) changed it to a count relative to the registry size. This is the only edit to an existing test.
- Gap found, not fixed here (outside the files this task may change): `zehn run` with an unknown function name prints `{"code": "E0302", "message": ...}` without `severity` or `phase`; the schema describes `check --json`, so it is outside the contract and listed in `docs/DIAGNOSTICS.md`.

## Revisit condition
When a diagnostic key must be removed, renamed or retyped (that is schema 2), or when `run`, `patch` and usage errors should share the envelope.
