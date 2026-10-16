# Zehn diagnostics: the contract

Tools that drive `zehn check --json` (models, editors, CI) can rely on what this page says. The
machine-readable form is `docs/diagnostics.schema.json` (JSON Schema draft-07). Every code, with
its explanation and one broken and one fixed program, is in `docs/ERRORS.md`; the same programs
live in `catalog/<CODE>/` and are tested.

## The envelope

`zehn check <file> --json` prints one JSON object. Its first key is `"schema"`, the version of
this contract (currently `1`).

```json
{
  "schema": 1,
  "ok": false,
  "diagnostics": [ ... ],
  "definitions": [ {"ref": "fn#473e", "kind": "fn", "name": "double"} ],
  "examples": {"passed": 0, "failed": 1, "results": [ {"fn": "double", "line": 2, "example": "...", "status": "fail", "diag": { ... }} ]}
}
```

- `diagnostics` holds the static findings. A failed example is *not* repeated there: its
  diagnostic is `examples.results[i].diag`.
- `ok` is true when no diagnostic has severity `error` and no example failed.

## The diagnostic object

Required: `code` (`E` or `W` plus four digits), `severity` (`error` or `warning`), `phase`
(`lex`, `parse`, `check`, `runtime`, `usage`, `patch`), `message`.

Optional, present where they mean something: `location` (`fn`, `line`, `clause`), `fix_hint`,
`blame` (`caller`, `callee`, `host`), `values`, `falls_through` (E0310), `call_stack` and
`fuel_limit` / `depth_limit` (E0801, E0802), `via_example` (a runtime diagnostic raised while an
example ran), and per-code extras such as `expected` and `found` (E0306) or `current_refs`
(E0701). The schema lists the common optional keys; every object also allows additional ones.

## Compatibility rule

**Within schema 1, keys are only ever added.** Concretely:

- a key that exists is never removed or renamed, and never changes type;
- a code is never reused for another meaning, and its severity does not change;
- new keys, new codes and new `phase` values may appear in any release, so a consumer must ignore
  what it does not know;
- the order of keys inside an object is not part of the contract, except that `schema` comes first
  in the envelope;
- removing, renaming or retyping a key, or reading a key differently, means `"schema": 2`.

## Known gaps (schema 1)

- `zehn run` with an unknown function name prints a diagnostic that has `code` and `message` but
  no `severity` or `phase`; it does not use the envelope and is outside this contract.
- Diagnostics printed by `run`, `patch` and usage errors are bare diagnostic objects (or a list of
  them), not wrapped in the envelope; they follow the diagnostic object above.
