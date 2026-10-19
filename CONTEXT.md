# Zehn - project context

Goal: Zehn is a language for LLMs as authors and humans as auditors (SPEC.md).
This repo is its single-file Python reference implementation (zehn.py, Python 3.9+, no dependencies).

## Status
Phase 1 closed (v0.4, ADR-0022); next: Phase 2 planning. Phase 0 leftovers: hidden set pending; baseline gate pending (ADR-0016 proposed, the builder has not decided; v0.3 baseline gemma-4-31b-it covers the first 30 tasks only).
Gate: H5 -0.013, CI [-0.040, 0.013]: the rule says "stop Phase 1, apply section 14" (ADR-0016, proposed; the builder decides).
Implementation lives in `zehnlib/`; `zehn.py` is a facade.
Build: `python3 -m compileall -q zehn.py zehnlib bench`. Test: `sh ci/run_ci.sh` (unit tests are `python3 -m unittest discover -s tests`).

## Working rules
1. Every language change = a SPEC edit + a test + a file in `examples/` + a file in `errors/`.
2. Every new error code has an `explain` text (the EXPLAIN table in zehn.py).
3. A breaking change needs an ADR in `DECISIONS/` and a version bump.
4. Never weaken, skip or delete an existing test unless the task says so.

## Session start
1. Read this file, then `_ops/STATE.md` (version, build, test, hazards).
2. Run the tests; the baseline is 337 green.
3. Read the part of SPEC.md the task touches and the ADRs about it.

## Session end
1. Run build and tests again and report the real output.
2. Update `_ops/STATE.md`: version +1, one history line, new decisions and hazards.
3. Write an ADR for each new design decision; `unmeasured` if no experiment was run.
4. Edit this file only if status or rules changed; keep it under 2,800 characters.

## Kit workflow
Rules for the receiving chat are in `_ops/RULES.md`. One project zip goes in and one zip comes out; `_ops/snap.sh` does before, after and pack.

## Pointers
- SPEC.md: the language (invariants: section 0, cost model: section 13)
- CHANGELOG.md: changes per version, "Decisions worth a second look"
- DECISIONS/: one ADR per design decision (ADR-0010 must be resolved in v0.4)
- bench/README.md: how the benchmark runs, reports and adds adapters
- The hidden task set lives outside the repository (`bench/hidden_set` is never zipped).
