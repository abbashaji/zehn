#!/usr/bin/env python3
"""Bet 1 review experiment: make | run | report.  Stdlib only, Python 3.9+.

  python3 bench/review.py make   --out bench/results/review-items.json
  python3 bench/review.py run    --items bench/results/review-items.json --model gemini:gemma-4-31b-it \
                                 --repeats 3 --run-id review-1 --yes
  python3 bench/review.py report --run bench/results/review-1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from benchlib import models, review, schema, stats  # noqa: E402
from benchlib.models import scheduler  # noqa: E402

ROOT = os.path.dirname(_HERE)


def cmd_make(args) -> int:
    tasks = schema.load_tasks(args.tasks_dir or [os.path.join(_HERE, "tasks")],
                              [x for v in (args.only or []) for x in v.split(",") if x] or None)
    items = review.build_items(tasks, seed=args.seed, log=lambda s: print(s, file=sys.stderr))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"seed": args.seed, "items": items}, f, indent=1)
    n_tasks = len({i["task_id"] for i in items})
    print("wrote %d items (%d tasks x %d arms x 2) to %s" % (len(items), n_tasks, len(review.ARMS), args.out))
    return 0


def _tasks_by_id(args) -> Dict[str, Any]:
    tasks = schema.load_tasks(args.tasks_dir or [os.path.join(_HERE, "tasks")], None)
    return {t["id"]: t for t in tasks}


def prune_errors(path: str) -> int:
    """Move records of failed API calls out of records.jsonl so that a resume redoes them (as run.py does)."""
    if not os.path.exists(path):
        return 0
    keep, bad = [], []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            try:
                (bad if json.loads(ln).get("error") else keep).append(ln if ln.endswith("\n") else ln + "\n")
            except ValueError:
                pass                      # a torn last line from a killed run
    if bad:
        with open(path[:-len(".jsonl")] + ".errors.jsonl", "a", encoding="utf-8", newline="\n") as f:
            f.writelines(bad)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(keep)
    return len(bad)


def _done(path: str) -> set:
    out = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if not r.get("error"):
                    out.add((r["item_id"], r["repeat"]))
    return out


def cmd_run(args, client=None) -> int:
    data = json.load(open(args.items, encoding="utf-8"))
    items = data["items"]
    if args.arm:
        items = [i for i in items if i["arm"] in args.arm]
    tasks = _tasks_by_id(args)
    run_dir = os.path.join(args.out, args.run_id)
    os.makedirs(run_dir, exist_ok=True)
    rec_path = os.path.join(run_dir, "records.jsonl")
    pruned = prune_errors(rec_path)
    if pruned:
        print("moved %d failed call(s) to records.errors.jsonl; they run again" % pruned)
    done = _done(rec_path)
    work = [(i, r) for r in range(1, args.repeats + 1) for i in items if (i["item_id"], r) not in done]
    if client is None and models.is_api_model(args.model) and not args.yes:
        raise SystemExit("remote models need --yes")
    lock = threading.Lock()
    clock = scheduler.Clock(1.0)
    if client is None:
        model = models.get_model(args.model, **({"max_output_tokens": 512}
                                                if models.is_remote_model(args.model) else {}))
        if models.is_remote_model(args.model):
            table = scheduler.load_limits(os.path.join(_HERE, "limits.json"))
            limits = scheduler.resolve_limits(args.model, table, {"rpm": None, "tpm": None, "rpd": None})
            quota = scheduler.QuotaState(os.path.join(run_dir, "quota_state.json"), clock)
            workers = scheduler.build_key_clients(model, limits, 0.9, 400, clock, quota, print)
        else:
            workers = [model]
    else:
        workers = [client]

    def execute(item, worker):
        it, rep = item
        task = tasks[it["task_id"]]
        base = {"item_id": it["item_id"], "task_id": it["task_id"], "category": it["category"],
                "arm": it["arm"], "kind": it["kind"], "repeat": rep, "model": args.model}
        try:
            reply = worker.complete(review.system_for(it["arm"]),
                                    [{"role": "user", "content": review.user_message(task, it["code"])}],
                                    args.temperature, {"task": task, "lang": it["arm"], "ext": "", "round": 1,
                                                       "ref_code": ""})
        except models.RunAborted:
            raise          # quota or a bad key: the pool requeues the item (as in loop.py)
        except Exception as ex:  # noqa: BLE001 - a call that failed after every retry is recorded, not fatal
            return dict(base, verdict=None, line=None, why="", in_tokens=0, out_tokens=0, correct=False,
                        located=False, answered=False, error="%s: %s" % (type(ex).__name__, ex))
        parsed = review.parse_reply(reply["text"])
        rec = {**base, "verdict": parsed["verdict"], "line": parsed["line"], "why": parsed["why"],
               "in_tokens": reply.get("in_tokens", 0), "out_tokens": reply.get("out_tokens", 0),
               "error": None}
        rec.update(review.score(it, parsed))
        return rec

    def on_record(rec):
        with lock:
            with open(rec_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    res = scheduler.run_pool(work, workers, execute, on_record, clock, args.time_budget_minutes, print)
    failed = 0
    if os.path.exists(rec_path):
        with open(rec_path, encoding="utf-8") as f:
            failed = sum(1 for ln in f if ln.strip() and '"error": null' not in ln)
    print("wrote %d record(s) to %s; remaining %d; failed_calls=%d" % (res.done, rec_path, len(res.remaining), failed))
    if res.fatal:
        print("FATAL: %s" % res.fatal, file=sys.stderr)
        return 2
    return 0


def load_records(run_dir: str) -> List[Dict[str, Any]]:
    out = []
    with open(os.path.join(run_dir, "records.jsonl"), encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                out.append(json.loads(ln))
    return out


def per_task(records, arm, field, kind) -> Dict[str, float]:
    """Mean of `field` per task for one arm and kind (averaged over repeats)."""
    acc: Dict[str, List[float]] = {}
    for r in records:
        if r["arm"] == arm and r["kind"] == kind and not r.get("error"):
            acc.setdefault(r["task_id"], []).append(1.0 if r[field] else 0.0)
    return {t: sum(v) / len(v) for t, v in acc.items()}


def summarize(records) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for arm in review.ARMS:
        rs = [r for r in records if r["arm"] == arm and not r.get("error")]
        if not rs:
            continue
        mut = [r for r in rs if r["kind"] == "mutated"]
        cl = [r for r in rs if r["kind"] == "clean"]
        out[arm] = {
            "runs": len(rs),
            "accuracy": sum(r["correct"] for r in rs) / len(rs),
            "detect": (sum(r["correct"] for r in mut) / len(mut)) if mut else float("nan"),
            "located": (sum(r["located"] for r in mut) / len(mut)) if mut else float("nan"),
            "false_alarm": (sum(r["verdict"] == "defect" for r in cl) / len(cl)) if cl else float("nan"),
            "unanswered": sum(not r["answered"] for r in rs),
            "tokens": sum(r["in_tokens"] + r["out_tokens"] for r in rs) / len(rs)}
    return out


def paired(records, a: str, b: str) -> Dict[str, Any]:
    """Accuracy difference a - b, paired by task (mean over mutated and clean item of the task)."""
    def acc(arm):
        m, c = per_task(records, arm, "correct", "mutated"), per_task(records, arm, "correct", "clean")
        return {t: (m[t] + c[t]) / 2 for t in m if t in c}
    xa, xb = acc(a), acc(b)
    ids = sorted(set(xa) & set(xb))
    va, vb = [xa[t] for t in ids], [xb[t] for t in ids]
    est, lo, hi = stats.paired_diff_ci(va, vb)
    return {"n": len(ids), "diff": est, "lo": lo, "hi": hi}


def cmd_report(args) -> int:
    recs = load_records(args.run)
    s = summarize(recs)
    lines = ["# Review experiment (Bet 1)", "", "run: `%s`, records: %d" % (args.run, len(recs)), "",
             "| arm | runs | accuracy | defect found | defect located | false alarm | unanswered | tokens/run |",
             "|---|---|---|---|---|---|---|---|"]
    for arm, v in s.items():
        lines.append("| %s | %d | %.3f | %.3f | %.3f | %.3f | %d | %.0f |" % (
            arm, v["runs"], v["accuracy"], v["detect"], v["located"], v["false_alarm"], v["unanswered"], v["tokens"]))
    lines += ["", "Paired by task (accuracy = mean of defect-found and clean-called-correct), 95% CI, 10,000 resamples:", "",
              "| comparison | tasks | accuracy diff | 95% CI | verdict |", "|---|---|---|---|---|"]
    for a, b in (("zehn", "python"), ("zehn", "python_examples"), ("python_examples", "python")):
        if a in s and b in s:
            p = paired(recs, a, b)
            win = "%s better" % a if p["lo"] > 0 else ("%s better" % b if p["hi"] < 0 else "no clear difference")
            lines.append("| %s - %s | %d | %+.3f | [%+.3f, %+.3f] | %s |" % (a, b, p["n"], p["diff"], p["lo"], p["hi"], win))
    lines += ["", "Rule: Zehn wins only if the CI of `zehn - python_examples` excludes 0 in its favour "
              "(the control that also shows examples). Runs with fewer than 50 tasks or 5 repeats are underpowered."]
    text = "\n".join(lines) + "\n"
    if args.out:
        open(args.out, "w", encoding="utf-8", newline="\n").write(text)
    print(text)
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="review.py", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--tasks-dir", action="append")
    m.add_argument("--only", action="append")
    m.add_argument("--seed", type=int, default=1234)
    m.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--items", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--repeats", type=int, default=5)
    r.add_argument("--temperature", type=float, default=0.0)
    r.add_argument("--arm", action="append", choices=review.ARMS)
    r.add_argument("--tasks-dir", action="append")
    r.add_argument("--out", default=os.path.join(_HERE, "results"))
    r.add_argument("--run-id", required=True)
    r.add_argument("--yes", action="store_true")
    r.add_argument("--time-budget-minutes", type=float)
    p = sub.add_parser("report")
    p.add_argument("--run", required=True)
    p.add_argument("--out")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return {"make": cmd_make, "run": cmd_run, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
