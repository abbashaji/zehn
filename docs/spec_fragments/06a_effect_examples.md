Target: SPEC.md section 7; action: add

### Mocked examples of effectful functions (dialect `effect_examples=mock`, unmeasured)

In v0.3 an effectful function cannot have an example (`E0602`) while `--strict` demands one (`E0402`). Under the dialect flag `effect_examples=mock` (default `off`) an example may carry a mock handler after its expression:

```
example-clause = "example" expr { "with" effect "=" "mock" list } [ "prints" list ] ;
```

```
example greet("Ada") with console = mock [] prints ["hello, Ada"]
example age(1900) == 126 with time.now = mock [2026]
```

- `with <effect> = mock [r1, r2, ...]` lists, in order, the results of the successive calls to that effect's functions. `time.now` yields the listed `Int`s. The functions of `console` return `Unit`, which has no literal, so the list of `console` is `[]` and calls to it never use up results.
- `prints [t1, t2, ...]` asserts the exact sequence of texts passed to `console.print`; it needs `with console = mock [...]`. A mismatch is `E0401`, with the printed and the expected texts in `values`.
- An example with mock clauses may have type `Unit` instead of `Bool` (a call run for its effects): it passes when it finishes and `prints` matches.
- A mocked example never touches the host and needs no `--grant`. It runs with the same fuel and depth limits as any example (section 13); the mock lists are evaluated inside that budget.
- Without the flag the clause is a parse error `E0201`. `zehn fmt` prints `with` clauses sorted by effect name, then `prints`, and round-trips them.
- Contracts (`requires`, `ensures`) and examples without a mock clause stay pure: calling an effectful function there is still `E0602`. Mock lists and `prints` lists are pure expressions too.

New errors (all under the flag):

| code | when | phase |
|---|---|---|
| `E0605` | the mock clauses are not exactly the effects the example needs: an effect declared in `uses` by a called function has no clause, a clause names an effect nobody uses, an effect has two clauses, or `prints` has no `console` clause | check |
| `E0606` | a function made more calls to an effect than its mock list has results (blame: caller) | runtime |
| `E0607` | a mock result does not have the result type of the effect's function (`time.now`: `Int`), or the list of a `Unit` effect is not empty | check |

Strict mode: a mocked example counts as an example like any other, so an effectful function now *can* satisfy `E0402`. Whether `--strict` should demand a mocked example for effectful functions is a build-time switch (`STRICT_NEEDS_MOCKED_EXAMPLE` in `zehnlib/passes/effect_examples.py`, default off); the literal rule makes the benchmark's reference solutions of category `effect` fail `--strict` (ADR-0015).

Limits: only user functions are mocked (an example that calls `console.print` or `time.now` directly is still `E0602`); the mock types come from the stdlib registry, so effects without stdlib functions (`fs`, `net`, `db`, `rand`, `clock`) accept only `[]`. Unused mock results are not an error.
