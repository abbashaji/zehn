#!/bin/sh
# Zehn CI pipeline. Plain sh, stops at the first failing step.
# Run from anywhere: sh ci/run_ci.sh
cd "$(dirname "$0")/.." || exit 1

IDS=$(grep -v '^[[:space:]]*#' ci/light_bench.txt | grep -v '^[[:space:]]*$' | tr -d '\r' | paste -sd, -)
TMP=$(mktemp -d "${TMPDIR:-/tmp}/zehn_ci.XXXXXX") || exit 1
trap 'rm -rf "$TMP"' EXIT

step() {
    echo
    echo "=== STEP $1 ==="
}

fail() {
    echo "CI FAILED at step: $1" >&2
    exit 1
}

step "1 compile"
python3 -m compileall -q zehn.py zehnlib bench || fail "1 compile"

step "2 unit tests (tests/)"
python3 -m unittest discover -s tests || fail "2 unit tests (tests/)"

step "3 bench tests (bench/tests)"
python3 -m unittest discover -s bench/tests || fail "3 bench tests (bench/tests)"

step "4 canonical form of examples (fmt --check)"
count=0
for f in examples/*.zehn; do
    [ -e "$f" ] || continue
    python3 zehn.py fmt "$f" --check || fail "4 fmt --check $f"
    count=$((count + 1))
done
for d in dialects/*/; do
    [ -d "$d" ] || continue
    flag=$(basename "$d")
    for f in "$d"examples/*.zehn; do
        [ -e "$f" ] || continue
        python3 zehn.py fmt "$f" --check --dialect "$flag" || fail "4 fmt --check $f (--dialect $flag)"
        count=$((count + 1))
    done
done
echo "step 4: $count file(s) in canonical form"

step "5 light benchmark replay (offline, proves harness and reference programs, not a model)"
python3 bench/run.py replay --only "$IDS" --lang zehn,python_plain --repeats 1 \
    --out "$TMP/replay" || fail "5 light benchmark replay"

step "6 light benchmark with a model (optional, never fails the pipeline)"
if [ -n "${ANTHROPIC_API_KEY:-}" ] && [ -n "${ZEHN_CI_MODEL:-}" ]; then
    mkdir -p ci/results
    RUN_ID="ci_$(date -u +%Y%m%dT%H%M%SZ)"
    if python3 bench/run.py run --only "$IDS" --models "anthropic:$ZEHN_CI_MODEL" \
        --lang zehn,python_plain --repeats 1 --yes --out ci/results --run-id "$RUN_ID"; then
        python3 bench/report.py --run "ci/results/$RUN_ID" || echo "step 6: report failed (ignored)"
    else
        echo "step 6: model run failed (ignored)"
    fi
else
    echo "step 6 skipped: set ANTHROPIC_API_KEY and ZEHN_CI_MODEL to run it"
fi

echo
echo "CI OK"
