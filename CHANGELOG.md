# Changelog

## v0.4

Closes Phase 1 (TASK_06a to 06m merged, TASK_08 acceptance). The language header is v0.4. In the default dialect, a v0.3 program behaves the same except that `--strict` no longer asks an effectful function for an example.

### Release notes (TASK_08)

- **Integer division is specified and stays as it is.** The A/B of `int_ops=explicit` (50 tasks, 3 repeats, gemma-4-31b-it) showed no gain (pass_repair 0.947 vs 0.947, CI [-0.053, 0.047]) and a cost (+0.33 repair rounds, +29% tokens), so `int_ops` stays `operators`. SPEC section 3 now defines `/` as floor division, `%` as `a - b * (a / b)` (sign of the divisor), the identity `a == (a / b) * b + a % b`, and `E0505` (blame: caller) for any zero divisor including `0 / 0`. New `examples/int_division.zehn`. ADR-0017 and ADR-0010 closed. Result is labelled underpowered (3 of 5 repeats).
- **`--strict` asks for an example only from pure functions (option B).** The A/B of `effect_examples=mock` (17 tasks, 3 repeats) showed no correctness gain (pass_repair 0.706 vs 0.740, CI [-0.111, 0.041]), so the default stays `off` and the contradiction between `E0402` and `E0602` is removed the other way: a function with `uses [...]` gets neither `E0402` nor `W0101`. `examples/effects.zehn` is now strict-clean. Explain texts of `E0402` and `W0101` and `docs/ERRORS.md` updated. ADR-0019 closed (underpowered).
- **SPEC catches up with the code.** Tuples (TASK_07, `E0313` to `E0318`) are merged into the grammar and section 3, the `run` argument rule into section 11; section 12 is rewritten as "v0.4 implementation status" with no open behaviour; the stale "no static recursion check" bullet is gone.
- **Acceptance** (roadmap section 5) is checked in ADR-0022: baseline published, recursion analysis without false positives on every example, no unspecified behaviour in the known limits, 300+ tests.
- Benchmark results of both experiments are kept in `bench/results/` (`effect_examples-*`, `int_division-*`), and the workflow `.github/workflows/experiments.yml` plus the adapter fix that stops the SPEC from leaking dialect text into the default arm (`bench/benchlib/adapters/zehn.py`) are part of this release.
- Tests: `tests/test_v04_acceptance.py` (16 tests); two assertions of `tests/test_effect_examples.py` changed because the strict default changed (reasons in the test comments); goldens regenerated only for `errors/bad_static` and `examples/effects`.

### Phase 1 branches

- **06a, mocked examples of effectful functions** (dialect `effect_examples=mock`, default `off`): `example E with <effect> = mock [..] prints [..]`; errors `E0605` (clauses do not match the effects the example needs, static pass `effect_examples` at order 420), `E0606` (mock list exhausted, run time), `E0607` (mock result of the wrong type); `zehn fmt` sorts the clauses; ADR-0019 (unmeasured), A/B experiment prepared in `bench/experiments/effect_examples/` (not run); 30 tests.
- **06b, unconditional recursion is a static error** (`E0311`, pass `recursion`, order 400): a call graph of certain calls, every cycle reported once, zero false positives by contract; `errors/bad_termination.zehn` now stops at `E0311`, its run-time twin is `errors/bad_termination_runtime.zehn` (`E0801` / `E0802`); ADR-0020; 42 tests including a 400-program soundness check.
- **06c, explicit Int division**: `int.div_floor`, `int.div_trunc`, `int.rem_euclid`; dialect `int_ops=operators|explicit` (default `operators`), under `explicit` the operators `/` and `%` are `E0312` (pass `int_ops`, order 410); experiment pack `bench/experiments/int_division/` (20 `numneg` tasks; `verify-refs --variant`); ADR-0017 (unmeasured, ADR-0010 stays open until TASK_08); 26 tests.
- **06d, diagnostics catalog and schema**: `catalog/<CODE>/` with `broken.zehn`, `fixed.zehn`, `meta.json` for all 43 codes, `zehn explain` text for `E0001` and the weak texts rewritten, `"schema": 1` in `check --json` with `docs/diagnostics.schema.json` and `docs/DIAGNOSTICS.md`, `tools/gen_error_docs.py` writes `docs/ERRORS.md`; ADR-0018; 18 tests.
- **06e, CI**: `sh ci/run_ci.sh` (compile, `tests/`, `bench/tests`, `fmt --check` of `examples/` and the dialect examples, offline light benchmark replay of `ci/light_bench.txt`, optional model step); `.github/workflows/ci.yml` only calls it (never executed here).

Merge notes: the pass registry is now `100 names, 200 types, 300 returns, 400 recursion, 410 int_ops, 420 effect_examples`; the new codes are `E0311`, `E0312`, `E0605` to `E0607`; the bench adapter and hidden-test runner now pass `--dialect` to `fmt` and to the run step (a gap found by 06a); 251 tests in `tests/` (135 + 116 new), 235 in `bench/tests`.

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
