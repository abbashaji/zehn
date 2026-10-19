# STATE
Name: Zehn
Version: 12
Return: full
Build: python3 -m compileall -q zehn.py zehnlib bench
Test: sh ci/run_ci.sh
Toolchain: python 3.12.3 in v010 and v009 (project requires 3.9+; 3.9 only syntax-checked); v008 merge had rustc/clippy 1.97.0, tsc 6.0.3, mypy 2.3.1, ruff 0.16.8
Baseline: v010 sandbox has no rustc/tsc/mypy/ruff: `sh ci/run_ci.sh` exit 0 = 251 + 235 tests OK, 52 bench tests skipped (toolchains), fmt --check 8 files, light replay 10 tasks x 2 languages OK; the v008 rustc 1.97 failure (test_toolchains RustTests.test_other_unknown_name_codes expects E0412, rustc 1.97 says E0425) was not re-run here; verify-refs 600 of 600 OK in v008

## Requirements
- Reference implementation of the Zehn language (Python 3.9+, no dependencies)
- 337 tests in tests/ stay green (251 baseline of v010, 70 tuples, 16 acceptance) (135 + 116 new in 06a to 06d: effect examples 30, recursion 42, int ops 26, catalog 18); bench/tests 235
- Roadmap: Zehn - Build Spec and Roadmap from v0.3 to v1.0

## Roadmap (optional; [ ] todo, [x] done)
- [ ] <item> - Done when: <one observable check>

## Decisions and why
- 20 ADRs in DECISIONS/ (ADR-0016 proposed, ADR-0020 measured, the rest unmeasured); CONTEXT.md is the session memory (<=2800 chars, unverified as 800 tokens)
- v0.4 decisions (ADR-0022): ADR-0010/0017 floor `/` `%` kept and specified (int_ops stays operators); ADR-0019 option B (strict asks examples only of pure functions), effect_examples stays off; both A/Bs underpowered (3 repeats)
- Merge v010 decisions: E0605 is a real static pass (420 effect_examples); ADRs of branches renumbered 0015->0019 (effect examples) and 0016->0020 (recursion); catalog E0802 broken.zehn is a guarded recursion (an unconditional one is now E0311); STRICT_NEEDS_MOCKED_EXAMPLE stays False (06a deviation 2, the builder may still choose); passes run 100 names, 200 types, 300 returns, 400 recursion, 410 int_ops, 420 effect_examples

## Known hazards / open issues
- Baseline (gemma-4-31b-it) is complete: 0 errored records left (API failures were redone by --resume); bench/results/ holds the baseline folder untouched (pilot folders not copied)
- Gate proposal in ADR-0016 (status proposed): the builder has not decided; SPEC.md size vs the 5,000-token cap is still unmeasured (no API key here)
- Zehn run pure_005 repeat 3 ended on E0203 twice although ADR-0014 should forgive it: unexplained
- Unreviewed: do the python/ts/rust strict tools have a layout-style asymmetry like E0203 (ADR-0014)?
- Pilot (6 tasks, gemma-4-31b-it) was run before ADR-0014: its zehn numbers are not comparable; python_strict/ts_strict/rust_strict layout checks were not reviewed for the same asymmetry
- Remote models: `gemini:`/`openai:` clients and the scheduler were tested only against local fake servers; Gemini facts not on Google's own pages: finish reason MAX_TOKENS, `thought` part flag, 429 body (see bench/README.md)
- Google limits apply per project, not per key: extra keys of one project add no quota; bench/limits.json Gemini rows come from the builder's account table
- A run that ends with an `error` record after 6 retries is recorded, so --resume does not redo it: check `status` (errored records)
- .github/workflows/baseline.yml was never executed (no GitHub here); runner tool versions unknown until its `doctor` step runs
- Code lives in zehnlib/ (largest parser.py 472 lines); zehn.py is a thin facade that must keep exporting: analyze parse Interp show to_value ZehnError DEFAULT_FUEL DEFAULT_DEPTH static_diags format_program definition_refs run_guarded main V Rec FnRef MapV eq, plus BUILTINS SIGS (now from zehnlib.stdlib) instantiate (tests/test_zehn.py uses them)
- Registries: a new stdlib fn / static pass (order 400-499) / command / dialect flag is one new file (see tests/test_registry.py DEMO_PLUGIN); explain and hint texts live only in zehnlib/explain_text.py; dialect state is process-wide (not thread-local) because analysis runs on a helper thread; E0001 from the CLI exits 2
- Tests that register temporary things must use snapshot_registries from tests/test_registry.py or they leak into other tests
- tests/golden/ (tests/test_golden.py): regenerate only entries you legitimately change with `python3 tests/test_golden.py --regen [program ...]`; fuel per example is pinned (cost model = language semantics)
- zehnlib.errors also holds DEFAULT_FUEL, DEFAULT_DEPTH, host_stack_error, run_guarded (avoids an interp<->analysis import cycle); zehnlib.cli carries the usage header and builds the usage lines from the command registry (alphabetical, and `--help` exits 0)
- Dev set is 100 tasks (17 each pure/text/domain/effect, 32 edit); difficulty skewed to level 3 by design, not measured: no model has run on tasks 007+ yet; hidden set still pending
- Newer clippy (1.97) is stricter than the 1.75 the branches used: text_010 ref.rs was changed to `rem_euclid` for clippy::manual_is_multiple_of; other refs may trip future lints
- tests read examples/ and errors/ flat: any subfolder in them breaks the tests
- Mock dialect: `hash`/`patch`/`lock` take no --dialect (mock files only work with check, fmt, run); E0606 blame is `caller`; a direct console.print / time.now call in an example stays E0602; the A/B experiments (effect_examples, int_division) have not been run (no API key)
- E0503 and E0603 are unreachable run-time guards (ADR-0018); docs/ERRORS.md is generated (`python3 tools/gen_error_docs.py`) and tests/test_catalog.py fails when it is stale; a new error code needs catalog/<CODE>/ and an explain text
- ci/run_ci.sh is the Test command; .github/workflows/ci.yml was never executed (no GitHub here); the tests print ResourceWarnings about unclosed files (not failures)
- Code charges fuel for big-int comparisons but SPEC section 13 does not list them (ADR-0004)
- SPEC invariant 2 says the parser rejects non-canonical layout; code only warns (ADR-0002)
- Phase 2 input: bench/notes/*_rejected.md (0 tasks rejected in every branch: 100 of 100 kept; the files list stdlib friction)
- Python 3.9 is only syntax-checked (ast feature_version); rust and clippy verified on 1.75 only, newer clippy may flag more; tsc was 7.0.2 in branch d, 6.0.3 in e and in the merge
- Toolchains (mypy, ruff, tsc, rust, clippy, rustfmt) were all installable in the branches and in the merge; none missing

## History (newest first, last 8, one line each)
- v012 (task 08): v0.4 acceptance: both A/B decisions (keep operators, keep mock off + strict option B in checker.py), SPEC v0.4 (tuples merged, division semantics, section 12 rewritten), examples/int_division.zehn, ADR-0022, ADR-0010/0017/0019 final, CHANGELOG v0.4, results of both experiments in bench/results; 337 tests
- v011 (task 07, branch on v010, not merged): tuples: `(a, b)` expressions and `case (x, y)` patterns, `Tup` value, E0313-E0318, tuple-aware exhaustiveness (E0301 with a witness), `run` JSON list per declared tuple type, ADR-0021 (the plan's 0019 was taken), spec fragment 07_tuples.md; 70 new tests (321 in tests/), golden: 60 files unchanged + 10 added for the two new programs; tests/test_walk.py SPEC_KINDS gained tuple/ptuple
- v010: merged 06a-e: effect_examples=mock dialect (E0605-E0607, pass 420), recursion analysis (E0311, pass 400), int division functions + int_ops dialect (E0312, pass 410) + int_division experiment pack, diagnostics catalog + schema 1 + ERRORS.md, CI (ci/run_ci.sh); spec fragments applied to SPEC.md; bench adapter passes --dialect; 251 tests
- v009: TASK_05 registries: stdlib (zehnlib/stdlib/, one module per namespace), static passes (100/200/300), explain/hint registry, commands (zehnlib/commands/), discover(), dialect flags (--dialect, no flag registered yet), nodes.walk; no behaviour change (golden + fuel unchanged); 55 tests
- v008: merged a-h: module split (zehnlib/, zehn.py facade, golden tests, 80 tests) + 70 new tasks (pure/text/domain/effect 007-017, edit 007-032) = 100 dev tasks, none rejected
- v007: Phase 0 baseline written up (bench/BASELINE_v0.3.md, ADR-0016 proposed); report.py --exclude-errors (explicit left-out table); 1 test
- v006: bench: API failures redone on --resume and left out of reports, optional round diags (ADR-0015); prune-errors command
- v005: bench zehn adapter forgives layout-only E0203 (ADR-0014) after the pilot; 2 tests
- v004: free remote baseline: gemini/openai clients, per-key rate scheduler, resume, status, doctor, time budget, baseline.yml, limits.json
- v003: merged a b c d e: 30 benchmark tasks (pure, text, domain, effect, edit; 6 each, refs in zehn, python, ts, rust), notes in bench/notes
