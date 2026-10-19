# Where Zehn could be a real winner (plan, not yet run)

Status after v0.4: on the *author* side Zehn only ties (H5 -0.013, CI [-0.040, 0.013]) and costs about 7x the
tokens (SPEC resent every round). Everything built so far measures "can a model write it". Zehn's actual claim is
different: "a human can **audit** it, and it **cannot do more than it says**". Neither half has been measured.

## Three bets, cheapest first

### Bet 1: Auditability (the claim that was never tested)
Question: given a program, how well does a reviewer find a planted defect, and how much does it cost?
- Material: for 40 existing tasks take the reference solution in Zehn, Python and Rust. Plant one defect per program
  (off-by-one, wrong sign, missing case, wrong rounding) in half of them; the other half stay clean.
- Reviewer: a model (cheap, fixed) and later 5 to 10 humans. Sees only the program, no tests. Says "defect: yes/no, where".
- Metrics: detection rate, false-alarm rate, tokens or minutes per verdict. Paired by task. Same A/B rule (`report.py ab`).
- Zehn wins if the contracts and examples let the reviewer find defects at a higher rate or lower cost than Python/Rust.
- Needs: a defect-planting script (mutation, there is already a mutant check in the int_division pack) and a new
  `review` mode in `bench/run.py`. No change to the language.

### Bet 2: Containment (agent safety)
Question: when a model writes an action program under a permission policy, how often does something outside the
policy actually happen?
- Tasks: 30 effect tasks plus a policy ("may print, may not read the clock/network/files") and, for half, an injected
  instruction in the task data ("also send the list to ...").
- Arms: Zehn (`uses` + `--grant`, `E0601` static, `E0604` at run time), plain Python (no check), Python with a
  hand-written allowlist wrapper (the fair strong baseline).
- Metrics: out-of-policy action executed (count), task still solved (pass), repairs needed.
- Zehn wins if out-of-policy executions are near 0 *and* pass_repair is not lower than the wrapper arm. If the wrapper
  arm also reaches 0, the language adds nothing here and this bet is dead: say so.
- Needs: out-of-policy probes in the hidden tests (a fake network/file layer that records calls).

### Bet 3: Cost fix (removes the main loss)
Question: can the 7x token cost go away?
- Prompt caching of SPEC.md, a shorter spec (target under 3,000 tokens), and a measured ablation of which SPEC sections
  the model actually needs. Metric: tokens per solved task vs python_strict, same pass_repair.
- Zehn wins on cost only if it gets within about 2x; otherwise the other bets must carry it.

## Decision rule (write it down before running)
- Run Bet 1 and Bet 2 with 1 stronger model, 40 tasks, 5 repeats. Not free-tier gemma only.
- Continue Zehn if at least one bet shows a CI excluding 0 in Zehn's favour and Bet 3 gets cost under 2x.
- If neither bet wins: stop developing the language; keep `bench/` (A/B harness, diagnostics loop) as the product.

## Risks stated up front
- The strongest baseline for Bet 2 is "Python plus a small allowlist wrapper"; if that matches Zehn, the language is not needed.
- Bet 1 with a model reviewer may not transfer to humans; run a small human check before believing it.
- One model family so far. A result on one model is a hint, not a finding.
