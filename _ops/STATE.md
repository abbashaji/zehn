# STATE
Name: Zehn
Version: 4
Return: full
Build: python3 -m compileall -q zehn.py bench
Test: python3 -m unittest discover -s tests && python3 -m unittest discover -s bench/tests
Toolchain: python 3.13.16 (project requires 3.9+; only 3.13 was run); rustc 1.97.0 in the v004 sandbox
Baseline: red on rustc 1.97 (302 tests, 1 fails, same on the untouched v3 tree: test_toolchains RustTests.test_other_unknown_name_codes expects E0412, rustc 1.97 says E0425); green on rustc 1.75 in v3

## Requirements
- Reference implementation of the Zehn language (Python 3.9+, no dependencies)
- 78 tests stay green
- Roadmap: Zehn - Build Spec and Roadmap from v0.3 to v1.0

## Roadmap (optional; [ ] todo, [x] done)
- [ ] <item> - Done when: <one observable check>

## Decisions and why
- 13 ADRs in DECISIONS/ (all unmeasured); CONTEXT.md is the session memory (<=2800 chars, unverified as 800 tokens)
- ADR-0010 (Int / and % use floor semantics) must be resolved in v0.4

## Known hazards / open issues
- Remote models: `gemini:`/`openai:` clients and the scheduler were tested only against local fake servers; Gemini facts not on Google's own pages: finish reason MAX_TOKENS, `thought` part flag, 429 body (see bench/README.md)
- Google limits apply per project, not per key: extra keys of one project add no quota; bench/limits.json Gemini rows come from the builder's account table
- A run that ends with an `error` record after 6 retries is recorded, so --resume does not redo it: check `status` (errored records)
- .github/workflows/baseline.yml was never executed (no GitHub here); runner tool versions unknown until its `doctor` step runs
- Single-file implementation: everything is in zehn.py (about 2,700 lines)
- tests read examples/ and errors/ flat: any subfolder in them breaks the tests
- E0001 has no EXPLAIN text (zehn explain E0001 says unknown code); needs a code task
- Code charges fuel for big-int comparisons but SPEC section 13 does not list them (ADR-0004)
- SPEC invariant 2 says the parser rejects non-canonical layout; code only warns (ADR-0002)
- Phase 2 input: bench/notes/*_rejected.md (0 tasks rejected in every branch: 30 of 30 kept; the files list stdlib friction)
- Python 3.9 is only syntax-checked (ast feature_version); rust and clippy verified on 1.75 only, newer clippy may flag more; tsc was 7.0.2 in branch d, 6.0.3 in e and in the merge
- Toolchains (mypy, ruff, tsc, rust, clippy, rustfmt) were all installable in the branches and in the merge; none missing

## History (newest first, last 8, one line each)
- v004: free remote baseline: gemini/openai clients, per-key rate scheduler, resume, status, doctor, time budget, baseline.yml, limits.json
- v003: merged a b c d e: 30 benchmark tasks (pure, text, domain, effect, edit; 6 each, refs in zehn, python, ts, rust), notes in bench/notes
- v002: merged branches a (runner), b (report), c (context, ADRs), d (ts_strict, rust, rust_strict adapters)
- v001: starting point
