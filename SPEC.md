# Zehn (ذهن) — Language Specification v0.3

A language designed for LLMs as the primary authors, and humans as auditors.

## 0. Design Invariants

1. **Plan before body.** Signature, intent, effects, contracts, examples come before the implementation.
2. **One canonical form.** Every program has exactly one valid text (formatter-enforced; the parser rejects non-canonical layout).
3. **Nothing implicit.** No implicit conversions, no null, no exceptions, no operator overloading, no macros, no globals.
4. **Explicit block ends.** Every block closes with `end <kind>`.
5. **Left-to-right dataflow.** Names are always introduced before use, in reading order.
6. **Machine-readable diagnostics.** Every error is JSON with code, location, cause, and fix hint.
7. **Determinism.** No undefined behavior. Map/set iteration order is insertion order.
8. **No silent holes, no hangs.** A function body must return on every path (checked statically, section 5). Every run is metered: runaway recursion or work ends in a diagnostic, never a hang or a host crash (section 13).

## 1. Lexical Structure

```
comment     = "--" { any-char-except-newline } ;
ident       = letter { letter | digit | "_" } ;        (* snake_case for values/fns *)
type-ident  = upper-letter { letter | digit } ;        (* PascalCase for types/variants *)
int         = digit { digit } ;
string      = '"' { char } '"' ;
```

Keywords: `fn type let var return if then else end match case do intent uses requires ensures example implies and or not true false`

Built-in constructors (not keywords, reserved names): `ok err some none`. Reserved identifiers: `out` and the stdlib namespaces `list text int option result map console time`.

Statements are separated by newlines. There are no semicolons and no significant indentation (indentation is canonicalized by the formatter, not parsed).

## 2. Grammar (EBNF)

```
program     = { type-decl | fn-decl } ;

type-decl   = "type" type-ident "=" variant { "|" variant } NEWLINE
            | "type" type-ident "=" "{" field { "," field } "}" NEWLINE ;
variant     = type-ident [ "(" type { "," type } ")" ] ;
field       = ident ":" type ;

fn-decl     = "fn" ident "(" [ param { "," param } ] ")" "->" type NEWLINE
              [ "intent" string NEWLINE ]
              [ "uses" "[" [ effect { "," effect } ] "]" NEWLINE ]
              { "requires" expr NEWLINE }
              { "ensures" expr NEWLINE }
              { "example" expr NEWLINE }
              "do" NEWLINE
              { stmt }
              "end" "fn" NEWLINE ;

param       = ident ":" type ;
type        = type-ident [ "<" type { "," type } ">" ] | "(" type { "," type } ")" ;
effect      = ident { "." ident } ;

stmt        = "let" ident [ ":" type ] "=" expr NEWLINE
            | "var" ident [ ":" type ] "=" expr NEWLINE
            | ident ":=" expr NEWLINE                  (* only on var *)
            | "return" expr NEWLINE
            | if-stmt | match-stmt | expr NEWLINE ;

if-stmt     = "if" expr "then" NEWLINE { stmt }
              [ "else" NEWLINE { stmt } ] "end" "if" NEWLINE ;

match-stmt  = "match" expr "do" NEWLINE
              { "case" pattern "=>" NEWLINE { stmt } }
              "end" "match" NEWLINE ;

pattern     = "_" | ident | int | string | "true" | "false"
            | type-ident [ "(" pattern { "," pattern } ")" ]
            | ( "ok" | "err" | "some" ) "(" pattern ")" | "none" ;

expr        = or-expr { "|>" call } ;
or-expr     = and-expr { "or" and-expr } ;
and-expr    = not-expr { "and" not-expr } ;
not-expr    = [ "not" ] implies-expr ;
implies-expr= cmp-expr [ "implies" cmp-expr ] ;
cmp-expr    = add-expr [ ( "==" | "!=" | "<" | "<=" | ">" | ">=" ) add-expr ] ;
add-expr    = mul-expr { ( "+" | "-" ) mul-expr } ;
mul-expr    = unary { ( "*" | "/" | "%" ) unary } ;
unary       = [ "-" ] postfix ;
postfix     = primary { "." ident | "(" args ")" | "?" } ;
primary     = int | string | "true" | "false" | ident | type-ident
            | "(" expr ")" | "[" [ expr { "," expr } ] "]"
            | "{" ident ":" expr { "," ident ":" expr } "}" ;
call        = postfix ;       (* in a pipeline, left value is inserted as FIRST argument *)
```

`|>` is pure syntax sugar: `a |> f(b)` parses to `f(a, b)` and `a |> f` to `f(a)`. Pipelines do not survive formatting (section 11): the canonical form is always nested calls.

There is no prime (`x'`) syntax: parameters are immutable, so their post-state equals their entry state. In `ensures`, the return value is named `out`.

Shadowing is forbidden: a name may be bound only once per scope chain (compile error `E0307`).
## 3. Types

- Primitives: `Int` (arbitrary precision), `Bool`, `Text`, `Unit`.
- Generic: `List<T>`, `Option<T>`, `Result<T, E>`, `Map<K, V>`.
- Records and sum types via `type`.
- Newtypes: `type Money = { cents: Int }`.
- No subtyping, no implicit conversion, no null. `Option<T>` is the only way to express absence.
- Types are checked statically (v0.2). Inference is local and bidirectional with unification:
  - `let` without annotation takes the type of its right-hand side; `[]`, `none` and `map.empty()` start with unknown element types that later uses (or an annotation, return type, or parameter type) fill in.
  - A record literal `{a: 1}` has no type name. Its type comes from the expected type if there is one, otherwise from the *unique* declared record type with exactly those fields; if several fit it is `E0309` and the fix is a type annotation.
  - Higher-order stdlib functions accept function types `Fn(A) -> B`, which only exist for named top-level fns (no lambdas, no function-typed parameters).
  - Type errors are `E0306` with `expected` / `found` fields; unknown/duplicate fields and non-record access are `E0308`; un-inferable types are `E0309`.

## 4. Mutability

- `let` is immutable, `var` is mutable and **local only** (a `var` cannot be captured, returned by reference, or passed as mutable).
- Passing a value to a function always passes an immutable (logically copied) value.
- A function that wants to "modify" returns a new value.
- No aliasing of mutable state exists, so no lifetimes are needed.

## 5. Errors

- No exceptions. Failure is `Result<T, E>`.
- `expr?` unwraps `ok(v)` to `v`, or returns `err(e)` from the enclosing function (the function's error type must match exactly; checked statically, `E0306`). Use `result.map_err` to convert error types. `?` on an `Option` needs an `Option`-returning function.
- `match` must be exhaustive; non-exhaustive match is compile error `E0301`.
- **Every path must return.** A body is accepted only if control can never reach its end: it must contain a `return`, or an `if` whose `then` *and* `else` both always return, or a `match` whose every case always returns. An `if` without `else` never counts. `?` can return early, but it never guarantees a return, so it does not count either. Violations are `E0310`, which lists *every* falling-through path in `falls_through` (`line` + `where`). A statement that follows a point that always returns can never run and is warning `W0102`. Zehn has no loops, so this analysis is exact, not conservative.
- Out-of-range `list.get` returns `none`. The operators `/` and `%` are partial: dividing by zero raises the defined diagnostic `E0505` (blame: caller), never undefined behavior. Guard with `requires b != 0`.
- **Unconditional recursion is rejected statically (`E0311`).** The static pass `recursion` (order 400) builds a call graph with an edge `f -> g` only when a call to the top-level function `g` is *certainly executed* whenever `f` runs up to that statement, and reports every cycle of that graph once (a function calling itself is a cycle of length 1). The diagnostic has `phase` `check`, `location {fn, line}` (the first function of the cycle and the line of its call), `cycle: [{"fn", "line"}, ...]` (the functions of the cycle in call order, each with the line of the call that leads to the next) and a `fix_hint`. Because `run` uses the same passes as `check`, a program with `E0311` never reaches its examples.
- **What counts as certain.** A call in a straight-line statement of the body (`let`, `var`, `:=`, expression statement, `return`); a call inside an argument of such a call or inside an operand of an arithmetic, comparison or `==` / `!=` / `not` / unary-minus expression; a call in the condition of an `if` or the subject of a `match`. It counts only while nothing earlier can leave the body: no `return` and no `?` before it in the same expression (arguments are evaluated left to right, then the callee) or in an earlier statement (an `if` or `match` that contains a `return` or a `?` anywhere ends the certain part).
- **What does not count.** Anything inside an `if` branch or a `match` case; the right operand of `and`, `or`, `implies`; anything after a `?` or a `return`; `requires`, `ensures` and `example` clauses; a function name used as a value (`list.map(xs, g)` is not a call); a call with the wrong number of arguments; a name hidden by a parameter, `let`, `var` or pattern binding of the same function. When unsure whether a call is certain, it is not counted.
- **Contract.** No false positives: a function that can return normally is never reported. The check is deliberately incomplete: endless recursion that is guarded by a condition is still caught only at run time, by `E0801` / `E0802` (section 13). Run-time errors that can end a run before the recursive call (division by zero, a failing `requires`, `unwrap` of an `err`) are not modelled: such a function is still reported, because it can never *return*.
- Error codes: add `E0311` (unconditional recursion) to the `E03xx` range.

## 6. Effects (capabilities)

- A function can only call functions whose effects are a subset of its own `uses`.
- Pure functions have `uses []` (or omit the line).
- Standard effects: `fs.read fs.write net.http db.read db.write time.now rand clock console`.
- Effects are checked statically (`E0601`): calling a fn, **or naming it as a value** (e.g. passing it to `list.map`), requires its effects to be a subset of the caller's `uses`. Contracts and examples must be pure (`E0602`).
- Effects are also enforced at runtime, in two independent layers:
  1. the running function must have declared the effect (`E0603`, blame callee);
  2. the host must have granted it (`zehn run ... --grant console,time.now`; default: nothing granted). Otherwise `E0604`, blame **host**.
  Examples always run with nothing granted.
- Effectful stdlib functions: `console.print(Text) -> Unit` needs `console`; `time.now() -> Int` needs `time.now` (Unix seconds; `--now N` fixes the clock so runs are reproducible). The other standard effects are reserved for later stdlib growth.
- `Unit` has no literal: a `-> Unit` function ends with `return <effectful call>`.

## 7. Contracts and Examples

- `requires P`: precondition. Evaluated on entry; failure → runtime error `E0501` blaming the **caller**.
- `ensures P`: postcondition. Evaluated on exit; failure → `E0502` blaming the **callee**. `out` names the return value.
- `example E`: executable test with `E : Bool`. Convention: computed call on the left, expected value on the right (`f(x) == expected`), so diagnostics can label `left` as actual. A failing example is `E0401`. A function with zero examples is warning `W0101`, or error `E0402` with `--strict`.
- Contracts and examples must be pure (`E0602` otherwise).
- `P implies Q` is `not P or Q`.
- `intent` is documentation, but its hash is stored with the contract set. `zehn lock <file>` writes `<file>.lock` with, per function, a fingerprint of the intent and a fingerprint of everything else (canonical text without comments or intent). If, relative to the lock, body/contracts/examples changed while `intent` is untouched, `zehn check` emits `W0201` (intent drift). Re-read the intent, then change it or run `zehn lock` again to confirm. Functions not in the lock are never reported.

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

Strict mode: a mocked example counts as an example like any other, so an effectful function now *can* satisfy `E0402`. Whether `--strict` should demand a mocked example for effectful functions is a build-time switch (`STRICT_NEEDS_MOCKED_EXAMPLE` in `zehnlib/passes/effect_examples.py`, default off); the literal rule makes the benchmark's reference solutions of category `effect` fail `--strict` (ADR-0019).

Limits: only user functions are mocked (an example that calls `console.print` or `time.now` directly is still `E0602`); the mock types come from the stdlib registry, so effects without stdlib functions (`fs`, `net`, `db`, `rand`, `clock`) accept only `[]`. Unused mock results are not an error.

## 8. Standard Library (core, deliberately tiny)

One function per job, always called qualified:

```
list.map  list.filter  list.fold  list.len  list.get(i) -> Option
list.append  list.concat  list.contains  list.sum
text.len  text.concat  text.split_on(sep)  text.contains  text.to_upper
int.to_text  int.abs  int.min  int.max
option.unwrap_or(default)  option.is_some
result.is_ok  result.is_err  result.unwrap  result.map
```

Added in v0.2:

```
option.map  result.map_err
map.empty  map.set  map.get  map.has  map.remove  map.keys  map.values  map.len
console.print  time.now                     (effectful, see section 6)
```

`Map<K, V>` is immutable and insertion-ordered: `map.set` on an existing key updates the value *in place* (position kept), `map.remove` drops the entry, `map.keys`/`map.values` follow insertion order. Keys may be any value (compared structurally). Map equality ignores order. `map.get` returns `Option<V>`. Full signatures live in `SIGS` in the reference implementation. Higher-order stdlib functions take a named top-level function (no lambdas).

No aliases. If two names could mean the same thing, only one exists.

### Explicit Int division (added by TASK_06c)

Three functions make the rounding of Int division visible in the name. All are `(Int, Int) -> Int`:

```
int.div_floor(a, b)     quotient rounded down toward negative infinity; same value as `a / b`
int.div_trunc(a, b)     quotient rounded toward zero (the fraction is dropped)
int.rem_euclid(a, b)    remainder r with 0 <= r < |b|; equals `a % b` only when b > 0
```

Examples: `int.div_floor(-7, 2) == -4`, `int.div_trunc(-7, 2) == -3`, `int.rem_euclid(-7, 2) == 1`,
`int.rem_euclid(7, -2) == 1` (while `7 % -2 == -1`). A zero divisor is `E0505`, blamed on the caller, exactly
like `/` and `%`. Fuel is the same as for the operators: the one step of the call expression, plus
`wa * wb` words when either operand is above 128 bits (`w = (bit_length >> 6) + 1`), charged before the work
and before the zero-divisor check. The floor remainder (`%` today) has no explicit name; there are no other
division functions.

The operators `/` and `%` keep their v0.3 meaning (floor semantics, ADR-0010) in the default dialect.

**Dialect `int_ops`** (`--dialect int_ops=operators|explicit`, default `operators`): under `explicit`
every `/` or `%` expression (in bodies, contracts and examples) is the error `E0312`; its `fix_hint` names the
three functions above. Under `operators` nothing changes. The flag exists to run an A/B experiment
(`bench/experiments/int_division/`); the decision between the options is ADR-0017 (status unmeasured).

New error code: `E0312` (operator `/` or `%` on Int under `int_ops=explicit`).

## 9. Diagnostics format

```json
{
  "code": "E0501",
  "severity": "error",
  "phase": "runtime",
  "message": "precondition failed",
  "blame": "caller",
  "location": {"fn": "transfer", "line": 4, "clause": "requires from.balance >= amount"},
  "values": {"from.balance": 10, "amount": 30},
  "fix_hint": "check the precondition before calling, or return err"
}
```

Error code ranges: `E01xx` lexing, `E02xx` parsing (`E0203` non-canonical layout under `--strict`), `E03xx` names, types, exhaustiveness and return paths (`E0306` mismatch, `E0308` record/field, `E0309` cannot infer, `E0310` path without `return`, `E0311` unconditional recursion, `E0312` `/` or `%` under `int_ops=explicit`), `E04xx` examples (`E0401` failed, `E0402` missing in strict), `E05xx` contracts at runtime, `E06xx` effects (`E0601` static, `E0602` impure contract, `E0603` undeclared at runtime, `E0604` not granted by host, `E0605` to `E0607` mocked examples under `effect_examples=mock`), `E07xx` patching, `E08xx` resource limits (`E0801` fuel, `E0802` call depth). `E0204` is "source nested too deeply to analyze"; `E0001` is a bad command-line option value. Warnings: `W0101` no example, `W0102` unreachable statement, `W0201` intent drift, `W0301` non-canonical layout.

### Stable diagnostics (schema 1)

The diagnostics are a versioned contract. `zehn check <file> --json` prints one object whose first key is `"schema": 1`, followed by `ok`, `diagnostics`, `definitions` and `examples` (the shape is `docs/diagnostics.schema.json`, JSON Schema draft-07; the prose is `docs/DIAGNOSTICS.md`). A diagnostic has the required keys `code`, `severity`, `phase`, `message` and the optional keys `location` (`fn`, `line`, `clause`), `fix_hint`, `blame`, `values`, `falls_through`, `call_stack`, `via_example`; every object also allows additional keys.

**Compatibility rule.** Within schema 1, keys are only ever added: no key is removed, renamed or retyped, a code is never reused for another meaning, and a consumer ignores keys and `phase` values it does not know. Removing, renaming or retyping a key means `"schema": 2`. The version lives in the envelope, once per output, not in each diagnostic.

**Catalog.** Every code has an explanation (`zehn explain <code>`, at most 60 words, naming the cause and the fix) and a catalog entry `catalog/<CODE>/` with `broken.zehn`, `fixed.zehn` and `meta.json`; `docs/ERRORS.md` is generated from them. `E0001` (bad command-line option) now has an explanation like every other code. `E0503` and `E0603` are defensive run-time guards that the static passes (`E0310`, `E0601`) make unreachable from `zehn check` and `zehn run`; their catalog entries say so.

## 10. Structural editing

Every top-level definition has a content hash. A **ref** is `fn#a3f9` or `type#c1d2`: the shortest prefix (at least 4 hex digits) of the SHA-256 of the definition's canonical text that is unique among definitions of that kind. Comments are not part of the hashed text, so editing a comment never changes a ref; any change to a signature, intent, clause or body does. `zehn check --json` and `zehn hash` list the current refs.

```
zehn patch <file> replace fn#a3f9 --with <file|->
zehn patch <file> delete  fn#a3f9
zehn patch <file> insert  --with <file|->
```

Rules: `--with` holds exactly one definition of the same kind as the target (`E0703`). A ref that matches nothing — including a stale ref after the definition was edited — is `E0701` and the error lists the current refs. An ambiguous prefix is `E0702` with candidates. The patched file is re-formatted and fully re-checked (types, effects, examples); without `--write` the result is printed, with `--write` it is written **only if the result has no errors**. Models therefore never produce line-number diffs, and a patch can never silently apply to a definition that changed underneath it.

## 11. Canonical form and tooling contract

`zehn fmt` prints the one canonical text of a program. Rules:

- two-space indentation; `intent`, `uses`, `requires`, `ensures`, `example` clauses in that order, each on its own line, between the signature and `do`;
- `uses [...]` is omitted when empty and sorted when not; types print as `Result<A, B>`;
- exactly one blank line between top-level definitions, no other blank lines; `case` is indented one level under `match`, its body one more;
- parentheses only where precedence needs them (`or` < `and` < `not` < `implies` < comparison < `+ -` < `* / %` < unary `-`; comparison and `implies` do not chain);
- `|>` pipelines are printed as nested calls;
- full-line comments stay attached to the next construct, trailing comments stay on their line.

`zehn check` reports a non-canonical file as `W0301`, or as error `E0203` with `--strict`.

```
zehn check  <file> [--json] [--strict] [--fuel N] [--max-depth N]
                                          parse, check names/types/effects/returns, run examples
zehn run    <file> <fn> <json-args> [--grant e1,e2] [--now N] [--fuel N] [--max-depth N]
zehn fmt    <file> [--write | --check]
zehn hash   <file> [--json]
zehn patch  <file> replace|delete|insert ...   (section 10)
zehn lock   <file>                        confirm intents (section 7)
zehn explain <code>                       long explanation of a diagnostic code
```

`run` arguments are JSON: numbers, strings, booleans, lists, and objects (records). Sum-type values, `ok/err/some/none` are written `{"$": "Rect", "args": [3, 4]}`.

Exit codes: 0 ok, 1 diagnostics with errors, 2 internal failure / usage.

## 12. v0.3 implementation status

- Implemented: lexer, parser, static checks (names, arity, `var`/`let`, no shadowing, effects incl. fn-as-value, exhaustiveness, `?` placement), static type checker, **static return-path analysis (`E0310`, `W0102`)**, evaluator, contracts, examples, JSON diagnostics, canonical formatter, content hashes and `patch`, intent-drift lock, runtime capability enforcement, **deterministic fuel and call-depth limits (`E0801`, `E0802`)**, `map.*`, `option.map`, `result.map_err`, `console.print`, `time.now`.
- Not implemented / known limits:
  - Tuple types parse but have no expressions; `Tuple` is only a type constructor.
  - `Int` division is floor division (Python semantics) and `%` has the sign of the divisor; this is deterministic but should be pinned down before v1.
  - `fs.*`, `net.http`, `db.*`, `rand`, `clock` effects have no stdlib functions yet.
  - Generic user types (`type Pair<A, B> = ...`) do not exist.
  - Non-termination is caught only *at run time*, by the budgets of section 13: a program whose examples pass can still exhaust fuel on other inputs. There is no static termination or unconditional-recursion check yet.
  - No tail-call optimization: recursion depth is bounded by `--max-depth` (default 10000).

## 13. Resource limits (fuel and call depth)

Zehn has no loops, so the only sources of unbounded work are recursion and large data. Both are bounded by two budgets that are properties of the *program's semantics*, not of the host: a run exhausts them at exactly the same point on every machine.

**Fuel** (`E0801`). One *entry point* gets `--fuel N` steps (default `1_000_000`). An entry point is: one `example`, one `zehn run`, one `Interp.invoke`. Budgets are never shared between entry points; contracts evaluated during a call spend the same budget as the call. Cost model:

| what | cost |
|---|---|
| every expression node evaluated, every statement executed | 1 |
| `+` `-` where an operand exceeds 128 bits | extra `max(wa, wb)` |
| `*` `/` `%` where an operand exceeds 128 bits | extra `wa * wb` |
| `list.append list.concat list.contains list.sum list.map list.filter list.fold text.concat text.split_on text.contains text.to_upper map.set map.get map.has map.remove map.keys map.values` | extra: sum of argument sizes |
| `int.to_text` | extra: argument size plus `w² / 4` (integer division, `w` of the argument) |
| everything else (`list.len`, `list.get`, `text.len`, `int.*`, `option.*`, `result.*`, `map.empty`, `map.len`, `console.print`, `time.now`) | none |

`w = ⌊bit_length / 64⌋ + 1`; *size* is the length of a list or text, the entry count of a map, or `⌊bit_length / 64⌋` of an `Int`. Big-integer cost is charged **before** the operation runs, so a runaway product is stopped before it allocates. Consequences: memory and wall-clock time are bounded. Because products cost `wa * wb`, a single `Int` can grow to only O(√fuel) words: repeated squaring stops at about 100 000 bits (30 000 decimal digits) with the default fuel, and `2000!` (5 736 digits) is well inside it. Larger numbers need a larger `--fuel`. The callbacks of `list.map/filter/fold` and `option.map`, `result.map`, `result.map_err` are ordinary calls and charge themselves.

**Call depth** (`E0802`). At most `--max-depth N` user functions may be active at once (default `10000`), counting calls made from stdlib callbacks. There is no tail-call optimization. A call beyond the limit raises `E0802`.

Both diagnostics have phase `runtime` and blame `callee`, and carry the data needed to find the cause without re-running:

```json
{
  "code": "E0802", "severity": "error", "phase": "runtime",
  "message": "call depth limit of 10000 exceeded",
  "blame": "callee",
  "location": {"fn": "spin", "line": 4},
  "depth_limit": 10000,
  "call_stack": {"depth": 10000, "innermost": [{"fn": "spin", "times": 12}],
                 "most_frequent": "spin", "most_frequent_count": 10000},
  "fix_hint": "function 'spin' is on the call stack 10000 times: check its base case; ..."
}
```

`innermost` is the last 12 frames run-length encoded, so mutual recursion shows up as an alternating `ping`/`pong` list. `E0801` has `fuel_limit` instead of `depth_limit`. Both appear under `via_example` when an example triggered them.

**Backstop.** If the *host's* own stack runs out first (only with pathologically nested expressions or values), the diagnostic is still `E0802`, without `call_stack`. A source file too deeply nested to parse is `E0204`. The reference implementation never lets a Python traceback escape. Raising the limits is the host's decision: `--fuel`, `--max-depth`.

A diagnostic is **not** a proof of non-termination, only of "did not finish within the budget"; the fix hint names the most frequent function on the stack as the first suspect.
