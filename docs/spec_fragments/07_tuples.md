Target: SPEC.md section 3; action: add

### Tuples (added by TASK_07)

A tuple keeps two or more values together. Tuples are always on (no dialect flag): they only add programs that were syntax errors before.

```
tuple-expr  = "(" expr "," expr { "," expr } ")" ;
tuple-pat   = "(" pattern "," pattern { "," pattern } ")" ;
tuple-type  = "(" type "," type { "," type } ")" ;          (* as before; now needs 2 or more *)
```

`(x)` stays a parenthesised expression. There is no empty tuple and no one-element tuple: `()`, `(x,)`, a pattern `(p)` and a type `(T)` are `E0318`. A tuple may stand wherever an expression, a pattern or a type may: signatures, `let`/`var` (with or without annotation), `return`, arguments, list elements, constructor fields (`Step((1, 2))`), `ok((a, b))`, nested tuples, and as the subject of `match`.

**One way to take a tuple apart: `match`.** `case (x, y) =>` binds one name per element (`_` and literals are allowed; a name may be bound once per pattern, `E0307`). There is no destructuring `let (a, b) = p` (`E0316`) and no access by position (`p.0`, `E0317`); the fix hint of both names the `match` form. `match (a, b) do ... end match` matches two values at once.

**Values.** A tuple is immutable. `==` and `!=` compare structurally, element by element, with the usual rule that `true` is not `1`; a tuple never equals a list. `show` (and `zehn run` output) prints `(1, "a")`, nested `(1, (true, 2))`. Ordering operators stay Int-only.

**Types.** The type of `(a, b)` is `(A, B)`. When the expected type is a tuple of the same size, each element is checked against its own element type, so a wrong element is an `E0306` on that element (`type mismatch in tuple element 2`). A tuple type of a different size than the one expected, at any place where two tuple types meet (a literal, a variable, an argument, a return), is `E0314`; a tuple pattern with a different number of elements than the matched tuple is `E0313`; a tuple pattern on a value that is not a tuple is `E0315`. Messages and the `expected` / `found` fields write tuple types as in the source, `(Int, Text)`.

**Exhaustiveness.** A `match` with tuple patterns is checked on the whole pattern tree: a case list is complete when every combination of the elements is covered. Constructors of a sum type, `ok`/`err`, `some`/`none` and `true`/`false` are enumerated; Int and Text literals never cover everything, so a `_` or a name is needed. A gap is `E0301` and the message shows one uncovered value, for example `missing (Red, false)` or `missing (none, some(_))`. A name, `_`, or a tuple of those is irrefutable, also inside a constructor (`some((a, b))` covers `some`).

**Fuel (section 13).** One step for the tuple node plus the steps of its element expressions, exactly like a list literal; building `(a, 1, a + 1)` costs 1 + 1 + 1 + 3 = 6. Matching a tuple pattern costs nothing beyond the steps of the `match` statement and its subject.

**`zehn run`.** A tuple argument is a JSON list of exactly its elements, read as a tuple only where the declared parameter type says so (also inside `List<(A, B)>`, `Option<(A, B)>`, records and constructor arguments): `zehn run f.zehn swap '[[1, "x"]]'`. Nested tuples nest lists: `'[[[0, 0], [3, 4]]]'`. A list of the wrong length, or a non-list, is `E0306` blamed on the caller. The result of `run` is printed with `show`, as for every other value, so a tuple result is `(2, 5)` text, not JSON.

New error codes: `E0313` (tuple pattern size), `E0314` (tuple size mismatch), `E0315` (tuple pattern on a non-tuple), `E0316` (destructuring `let`), `E0317` (positional access), `E0318` (empty or one-element tuple). `E0316` to `E0318` are parse errors; the others are reported by the checker.

Known limit: the unconditional-recursion check (`E0311`, section 5) does not look through the elements of a tuple, so `return (f(n), 1)` inside `f` is not reported statically; the fuel and depth limits still catch it.

Merge notes for the other sections (a fragment has one target): in section 2 add `tuple-expr` as an alternative of `primary`, `tuple-pat` as an alternative of `pattern`, and make the `type` production `"(" type "," type { "," type } ")"`; in section 12 delete the bullet "Tuple types parse but have no expressions; `Tuple` is only a type constructor."; in section 11 add the `run` argument rule above.
