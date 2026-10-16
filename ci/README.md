# CI

`sh ci/run_ci.sh` is the pipeline (plain sh, stops at the first failing step and names it); `.github/workflows/ci.yml` only calls it.
Steps: compile, `tests/`, `bench/tests`, `fmt --check` on `examples/*.zehn` and `dialects/<flag>=<value>/examples/*.zehn`, offline light benchmark replay.
The ten benchmark ids are in `light_bench.txt` (two per category, one level 1 and one level 3); replay proves the harness and reference programs, not a model.
Step 6 runs only if `ANTHROPIC_API_KEY` and `ZEHN_CI_MODEL` are set: same ids, results in `ci/results/` (git-ignored), report printed, never fails the pipeline.
Python 3.9+ and the standard library only; `ci.yml` was never executed here (no GitHub), so it is unverified.
