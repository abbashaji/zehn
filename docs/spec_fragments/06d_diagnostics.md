Target: SPEC.md section 9; action: add

### Stable diagnostics (schema 1)

The diagnostics are a versioned contract. `zehn check <file> --json` prints one object whose first key is `"schema": 1`, followed by `ok`, `diagnostics`, `definitions` and `examples` (the shape is `docs/diagnostics.schema.json`, JSON Schema draft-07; the prose is `docs/DIAGNOSTICS.md`). A diagnostic has the required keys `code`, `severity`, `phase`, `message` and the optional keys `location` (`fn`, `line`, `clause`), `fix_hint`, `blame`, `values`, `falls_through`, `call_stack`, `via_example`; every object also allows additional keys.

**Compatibility rule.** Within schema 1, keys are only ever added: no key is removed, renamed or retyped, a code is never reused for another meaning, and a consumer ignores keys and `phase` values it does not know. Removing, renaming or retyping a key means `"schema": 2`. The version lives in the envelope, once per output, not in each diagnostic.

**Catalog.** Every code has an explanation (`zehn explain <code>`, at most 60 words, naming the cause and the fix) and a catalog entry `catalog/<CODE>/` with `broken.zehn`, `fixed.zehn` and `meta.json`; `docs/ERRORS.md` is generated from them. `E0001` (bad command-line option) now has an explanation like every other code. `E0503` and `E0603` are defensive run-time guards that the static passes (`E0310`, `E0601`) make unreachable from `zehn check` and `zehn run`; their catalog entries say so.
