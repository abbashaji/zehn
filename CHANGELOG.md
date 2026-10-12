# Changelog

## v0.3

Closes the two "silent hole" items from the v0.2 known-limits list: a function that can fall off its end, and runs that never finish.

- **Static return-path analysis** (`E0310`, `W0102`): every path through a body must end in `return`. `E0310` lists *every* falling-through path (`falls_through: [{line, where}]`), not just the first. A statement after an always-returning point is warning `W0102`. Zehn has no loops, so the analysis is exact. `check` and `run` now share one `static_diags` pipeline, so `run` can no longer execute a program that `check` rejects. The run-time `E0503` stays only as a defence-in-depth guard.
- **Deterministic fuel** (`E0801`): one step per expression/statement, plus size-proportional charges for list/text/map operations and big-integer arithmetic (charged *before* the operation, so runaway products are stopped before they allocate). Budget is per entry point: each example and each `run` gets a fresh one. Cost model is specified in SPEC section 13.
- **Call-depth limit** (`E0802`, default 10 000). Diagnostics carry a `call_stack` summary (innermost 12 frames, run-length encoded, most frequent function) and a hint naming the first suspect.
- `--fuel N` and `--max-depth N` for `check` and `run`; `Interp.invoke()` as the public entry point (fresh budget, big-enough stack, no raw `RecursionError`).
- No Python traceback can escape any more: host-stack exhaustion is `E0802`, an unparseably nested source is `E0204`, a bad option value is `E0001` (exit 2).
- `int.to_text` and `show` work for integers beyond Python's 4300-digit default (fuel bounds the size instead).
- New: `examples/recursion.zehn`, `errors/bad_return.zehn`, `errors/bad_termination.zehn`; 38 new tests (78 total).

### Decisions worth a second look

1. **Defaults**: fuel 1 000 000 and depth 10 000. At these values `fib(40)` by double recursion is `E0801` after ~1 s, while `sum_to(5000)` by plain recursion passes. If you would rather make deep non-tail recursion impossible, lower the depth.
2. **`W0102` is a warning**, not an error, and `--strict` does not promote it. Dead code is a smell, not a hole.
3. **Big-integer cost is schoolbook (`wa * wb`)**, an upper bound on what CPython really does. The price is that integers top out near 100 000 bits at default fuel; the alternative (linear cost) allowed multi-second runs.
4. **Blame for `E0801`/`E0802` is `callee`**, since the usual cause is a missing base case. If a legitimately large input hits the limit, the fix is on the host side (`--fuel`).

### Still open

Non-termination is only caught at run time. A static "unconditional recursion" check (a call cycle in which no call sits under an `if`/`match`/short-circuit) would catch `fn f(n) = f(n)` before any example runs.

## v0.2

Closes every item that SPEC v0.1 §12 listed as "not implemented" except tuple expressions.

- **Static type checker** (`E0306`, `E0308`, `E0309`): bidirectional inference with unification; generic stdlib signatures; `?` error-type matching; record literals resolved from expected type.
- **Canonical formatter** (`zehn fmt`, `W0301` / `E0203`): one text per program, minimal parentheses, comments preserved, pipelines desugared.
- **Content hashes and structural patching** (`zehn hash`, `zehn patch replace|delete|insert`, `E0701`–`E0703`): stale refs are rejected, bad patches are never written.
- **Intent drift** (`zehn lock`, `W0201`).
- **Runtime capability enforcement** (`E0603`, `E0604`, `zehn run --grant`, `--now`); a function named as a value now needs its effects too.
- **Stdlib**: `map.*`, `option.map`, `result.map_err`, `console.print`, `time.now`.
- `zehn run` accepts variants as `{"$": "Ctor", "args": [...]}`.
- Duplicate `type` / constructor names are `E0202`.
- Test-suite (`tests/`, 40 tests), examples (`examples/`) and deliberately broken programs (`errors/`).

### Decisions worth a second look

1. The canonical form **desugars `|>`** into nested calls, so `transfer.zehn` was rewritten by `zehn fmt`. The alternative (print a call chain as a pipeline) is possible but is a bigger design choice.
2. Non-canonical layout is a **warning** by default and an **error under `--strict`**. SPEC invariant 2 says the parser rejects it; this keeps hand-written files usable.
3. `console` and `time` became reserved namespaces, because capability enforcement needs at least one effectful stdlib function to be real.
