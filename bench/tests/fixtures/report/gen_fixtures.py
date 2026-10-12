#!/usr/bin/env python3
"""Generate the synthetic result records used by the report tests.

Run:  python3 gen_fixtures.py     (writes the run_* folders next to this file)

The generated files are committed; this script documents how they were made
and gives each one a known truth:
  run_a        mixed small effects (all verdicts inconclusive), H5 estimate negative
  run_good     zehn clearly better than every baseline (H1-H5 supported)
  run_rounds   zehn needs clearly fewer repair rounds than python_strict (H2 supported)
  run_bad      zehn clearly worse than every baseline (H1-H5 refuted)
  run_ratio    zehn pass@1 is exactly 0.8 of python_plain (16/20 vs 20/20 tasks)
  run_same     identical data to run_same_b (paired difference must be exactly 0)
"""
from __future__ import annotations

import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_ROUNDS = 3


def clamp(p):
    return max(0.0, min(1.0, p))


def make_record(rng, run_id, task_idx, n_tasks, lang, variant, model, repeat, par):
    task_id = "t%03d" % task_idx
    category = ("algo", "text", "data")[task_idx % 3]
    trivial = task_idx % 10 == 0
    impossible = task_idx % 10 == 9
    rounds = []
    accepted = None
    last_pass = False
    first_pass = False
    tin = 0
    tout = 0
    for i in range(1, MAX_ROUNDS + 1):
        if trivial:
            ok_prog = True
        elif impossible:
            ok_prog = False
        else:
            ok_prog = rng.random() < clamp(par["p1"] if i == 1 else par["pr"])
        if trivial:
            tool_ok = True
        elif ok_prog:
            tool_ok = rng.random() < par["okpass"]
        else:
            tool_ok = rng.random() < par["s"]
        ndiag = 0 if tool_ok else rng.randint(1, 3)
        diags = ["E%04d" % rng.choice([101, 205, 301, 402, 801]) for _ in range(ndiag)]
        unknown = sum(1 for _ in diags if rng.random() < par["halluc"])
        r_in = int(par["tok_in"] * (1 + 0.3 * (i - 1)) * rng.uniform(0.8, 1.2))
        r_out = int(par["tok_out"] * rng.uniform(0.8, 1.2))
        rounds.append({"i": i, "tool_ok": tool_ok, "diag_codes": diags,
                       "unknown_names": unknown, "in_tokens": r_in, "out_tokens": r_out})
        tin += r_in
        tout += r_out
        if i == 1:
            first_pass = ok_prog
        last_pass = ok_prog
        if tool_ok:
            accepted = i
            break
    total = 5
    passed = total if last_pass else rng.randint(0, total - 1)
    return {
        "schema": 1, "run_id": run_id, "set": "dev" if task_idx % 2 == 0 else "hidden",
        "task_id": task_id, "category": category, "kind": "write",
        "lang": lang, "variant": variant, "model": model, "repeat": repeat,
        "temperature": 0.2, "rounds": rounds, "accepted_round": accepted,
        "first_try_pass": first_pass, "final_pass": last_pass,
        "final_tests": {"passed": passed, "total": total},
        "total_in_tokens": tin, "total_out_tokens": tout,
        "wall_ms": int(rng.uniform(800, 9000)), "error": None,
    }


def P(p1, pr, s, okpass, tok_in, tok_out, halluc):
    return dict(p1=p1, pr=pr, s=s, okpass=okpass, tok_in=tok_in, tok_out=tok_out, halluc=halluc)


PLAIN = P(0.60, 0.60, 1.0, 1.0, 900, 500, 0.0)

SCENARIOS = {
    "run_a": dict(seed=11, tasks=20, models=["m1", "m2"], repeats=3, groups={
        ("python", "plain"): PLAIN,
        ("python", "strict"): P(0.62, 0.72, 0.25, 0.97, 1600, 700, 0.15),
        ("rust", "strict"): P(0.58, 0.72, 0.20, 0.95, 2000, 900, 0.20),
        ("zehn", "default"): P(0.58, 0.70, 0.22, 0.95, 1500, 700, 0.12),
    }),
    "run_good": dict(seed=21, tasks=30, models=["m1"], repeats=4, groups={
        ("python", "plain"): PLAIN,
        ("python", "strict"): P(0.60, 0.70, 0.35, 0.80, 1800, 800, 0.20),
        ("rust", "strict"): P(0.45, 0.60, 0.15, 0.95, 2200, 900, 0.25),
        ("zehn", "default"): P(0.80, 0.95, 0.03, 0.99, 900, 400, 0.05),
    }),
    "run_rounds": dict(seed=51, tasks=30, models=["m1"], repeats=4, groups={
        ("python", "plain"): PLAIN,
        ("python", "strict"): P(0.65, 0.70, 0.20, 0.50, 1800, 800, 0.20),
        ("rust", "strict"): P(0.60, 0.70, 0.20, 0.60, 2200, 900, 0.25),
        ("zehn", "default"): P(0.65, 0.70, 0.20, 0.99, 1800, 800, 0.20),
    }),
    "run_bad": dict(seed=31, tasks=30, models=["m1"], repeats=4, groups={
        ("python", "plain"): P(0.85, 0.85, 1.0, 1.0, 900, 500, 0.0),
        ("python", "strict"): P(0.75, 0.90, 0.05, 0.98, 1000, 450, 0.05),
        ("rust", "strict"): P(0.70, 0.92, 0.04, 0.97, 1400, 600, 0.08),
        ("zehn", "default"): P(0.40, 0.45, 0.45, 0.80, 2400, 1100, 0.30),
    }),
}


def write_run(name, records):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "records.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")


def gen_random(name, sc):
    rng = random.Random(sc["seed"])
    recs = []
    for (lang, variant), par in sorted(sc["groups"].items()):
        for task in range(sc["tasks"]):
            for model in sc["models"]:
                for rep in range(1, sc["repeats"] + 1):
                    recs.append(make_record(rng, name, task, sc["tasks"], lang, variant, model, rep, par))
    write_run(name, recs)
    return recs


def det_record(run_id, task_idx, lang, variant, repeat, passed):
    """A deterministic one-round record that either passes or fails everything."""
    return {
        "schema": 1, "run_id": run_id, "set": "dev", "task_id": "t%03d" % task_idx,
        "category": ("algo", "text")[task_idx % 2], "kind": "write", "lang": lang,
        "variant": variant, "model": "m1", "repeat": repeat, "temperature": 0.2,
        "rounds": [{"i": 1, "tool_ok": True, "diag_codes": [], "unknown_names": 0,
                    "in_tokens": 1000, "out_tokens": 500}],
        "accepted_round": 1, "first_try_pass": passed, "final_pass": passed,
        "final_tests": {"passed": 5 if passed else 0, "total": 5},
        "total_in_tokens": 1000, "total_out_tokens": 500, "wall_ms": 1000, "error": None,
    }


def gen_ratio():
    """python_plain passes 20/20 tasks, zehn 16/20, both on 2 repeats: ratio 0.8."""
    recs = []
    for task in range(20):
        for rep in (1, 2):
            recs.append(det_record("run_ratio", task, "python", "plain", rep, True))
            recs.append(det_record("run_ratio", task, "zehn", "default", rep, task < 16))
    write_run("run_ratio", recs)


def gen_same():
    rng = random.Random(41)
    recs = []
    for lang, variant, par in (("python", "plain", PLAIN),
                               ("zehn", "default", P(0.6, 0.8, 0.1, 0.95, 1200, 600, 0.1))):
        for task in range(20):
            for rep in (1, 2, 3):
                recs.append(make_record(rng, "run_same", task, 20, lang, variant, "m1", rep, par))
    write_run("run_same", recs)
    copy = [dict(r, run_id="run_same_b") for r in recs]
    write_run("run_same_b", copy)


def main():
    for name, sc in SCENARIOS.items():
        gen_random(name, sc)
    gen_ratio()
    gen_same()


if __name__ == "__main__":
    main()
