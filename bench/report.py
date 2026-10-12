#!/usr/bin/env python3
"""Benchmark report: tables, H1-H5 verdicts and the A/B decision helper.

  python3 bench/report.py --run DIR [--run DIR ...] [--out FILE] [--set dev|hidden]
  python3 bench/report.py ab --a DIR --b DIR --simpler a|b [--out FILE]

Reads result records only (<DIR>/records.jsonl, optional <DIR>/meta.json).
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchlib import metrics, stats  # noqa: E402


def _num(x, fmt):
    if x != x:
        return "n/a"
    txt = fmt % x
    return txt[1:] if txt.startswith("-") and float(txt) == 0 else txt  # no "-0.000"


def f3(x):
    return _num(x, "%.3f")


def f1(x):
    return _num(x, "%.1f")


def fmt_metric(name, x):
    return f1(x) if name == "total_tokens" else f3(x)


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return lines


def load(dirs, only_set=None):
    metas = []
    records = []
    infos = []
    for d in dirs:
        meta, recs = metrics.load_run(d)
        if only_set:
            recs = [r for r in recs if r.get("set") == only_set]
        metas.append(meta)
        records.extend(recs)
        infos.append((d, meta, recs))
    return metas, records, infos


def build_report(dirs, only_set=None):
    metas, records, infos = load(dirs, only_set)
    max_rounds = metrics.infer_max_rounds(records, metas)
    out = ["# Benchmark report", ""]

    out += ["## Runs", ""]
    rows = []
    for d, meta, recs in infos:
        run_ids = sorted(set(str(r["run_id"]) for r in recs))
        sets = sorted(set(str(r["set"]) for r in recs))
        meta_txt = ", ".join("%s=%s" % (k, meta[k]) for k in sorted(meta)) or "-"
        rows.append([os.path.basename(os.path.normpath(d)), ", ".join(run_ids) or "-",
                     ", ".join(sets) or "-", len(recs),
                     len(set(r["task_id"] for r in recs)), meta_txt])
    out += table(["dir", "run_id", "set", "records", "tasks", "meta"], rows)
    out += ["", "max_rounds used for censoring: %d" % max_rounds,
            "Bootstrap: %d resamples over tasks, seed %d, 95%% percentile interval." % (
                stats.DEFAULT_N, stats.DEFAULT_SEED)]
    if only_set:
        out.append("Only records with set=%s." % only_set)
    out.append("")

    # per (lang, variant, model)
    groups = {}
    for r in records:
        groups.setdefault(metrics.group_key(r), []).append(r)
    out += ["## Results per language, variant and model", ""]
    header = ["lang", "variant", "model", "tasks", "runs"] + [metrics.METRIC_LABELS[m] for m in metrics.METRICS]
    rows = []
    for key in sorted(groups):
        s = metrics.summarize(groups[key], max_rounds)
        cells = [key[0], key[1], key[2], s["n_tasks"], s["n_runs"]]
        for m in metrics.METRICS:
            txt = fmt_metric(m, s[m])
            if m == "repair_rounds":
                txt += " (censored %d/%d)" % (s["censored"], s["n_runs"])
            cells.append(txt)
        rows.append(cells)
    out += table(header, rows)
    out.append("")

    # per category
    out += ["## Per category (models pooled)", ""]
    cats = {}
    for r in records:
        cats.setdefault((r["category"], r["lang"], r["variant"]), []).append(r)
    rows = []
    for key in sorted(cats):
        s = metrics.summarize(cats[key], max_rounds)
        rows.append([key[0], key[1], key[2], s["n_tasks"], s["n_runs"],
                     f3(s["pass_at_1"]), f3(s["pass_repair"]), f3(s["silent_bug_rate"])])
    out += table(["category", "lang", "variant", "tasks", "runs", "pass@1", "pass_repair", "silent-bug rate"], rows)
    out.append("")

    # hypotheses
    out += ["## Hypotheses H1 to H5", ""]
    hyps = metrics.evaluate_hypotheses(records, max_rounds)
    rows = []
    for h in hyps:
        verdict = h["verdict"] + (" (underpowered)" if h["underpowered"] else "")
        ci = "n/a" if h["lo"] != h["lo"] else "[%s, %s]" % (f3(h["lo"]), f3(h["hi"]))
        rows.append([h["id"], h["desc"], f3(h["est"]), ci, h["n_tasks"], h["repeats"], verdict])
    out += table(["H", "comparison", "estimate", "95% CI", "tasks", "repeats", "verdict"], rows)
    out += ["", "Underpowered = fewer than %d tasks or fewer than %d repeats (smallest "
            "(task, lang, variant, model) cell)." % (metrics.MIN_TASKS, metrics.MIN_REPEATS),
            "A bare language name (zehn) matches every variant of that language.", ""]
    h5 = hyps[4]
    if h5["est"] == h5["est"] and h5["est"] < 0:
        out += ["GATE: H5 point estimate is worse than rust_strict", ""]

    # stability
    out += ["## Stability", "",
            "Variance of first_try_pass across repeats (population variance), averaged over tasks.", ""]
    rows = []
    for key in sorted(groups):
        recs = groups[key]
        ser = metrics.task_series(recs, "stability", max_rounds)
        flaky = sum(1 for v in ser.values() if v > 0)
        rows.append([key[0], key[1], key[2], len(ser), f3(stats.mean(ser.values())),
                     flaky, metrics.min_repeats(recs)])
    out += table(["lang", "variant", "model", "tasks", "stability", "tasks with variance > 0", "repeats"], rows)
    out.append("")

    # calibration lists
    out += ["## Calibration", "",
            "Unsolved = no run of any language has final_pass. Solved by all = every run of "
            "every language has final_pass.", ""]
    by_task = {}
    for r in records:
        by_task.setdefault(r["task_id"], []).append(r)
    unsolved = sorted(t for t, rs in by_task.items() if not any(r["final_pass"] for r in rs))
    solved_all = sorted(t for t, rs in by_task.items() if all(r["final_pass"] for r in rs))
    out.append("Tasks no language solved (%d): %s" % (len(unsolved), ", ".join(unsolved) or "none"))
    out.append("")
    out.append("Tasks every language solved (%d): %s" % (len(solved_all), ", ".join(solved_all) or "none"))
    out.append("")
    return "\n".join(out)


def build_ab(dir_a, dir_b, simpler):
    ma, ra = metrics.load_run(dir_a)
    mb, rb = metrics.load_run(dir_b)
    max_rounds = metrics.infer_max_rounds(ra + rb, [ma, mb])
    out = ["# A/B comparison", "",
           "A = %s, B = %s, simpler option = %s" % (
               os.path.basename(os.path.normpath(dir_a)),
               os.path.basename(os.path.normpath(dir_b)), simpler),
           "Paired over tasks (repeats, models and cells averaged first); difference = A - B; "
           "%d resamples, seed %d, 95%% CI." % (stats.DEFAULT_N, stats.DEFAULT_SEED), ""]
    rows = []
    results = {}
    for m in metrics.METRICS:
        res = metrics.paired(ra, rb, m, max_rounds, "diff")
        results[m] = res
        ci = "n/a" if res["lo"] != res["lo"] else "[%s, %s]" % (fmt_metric(m, res["lo"]), fmt_metric(m, res["hi"]))
        rows.append([metrics.METRIC_LABELS[m], fmt_metric(m, res["a"]), fmt_metric(m, res["b"]),
                     fmt_metric(m, res["est"]), ci, res["n_tasks"]])
    out += table(["metric", "A", "B", "A - B", "95% CI", "tasks"], rows)
    out.append("")
    dm = results["pass_repair"]
    if dm["n_tasks"] == 0 or dm["lo"] != dm["lo"]:
        raise metrics.RecordError("A and B share no task, cannot compare")
    if dm["lo"] > 0:
        out.append("DECISION: a wins (pass_repair CI excludes 0)")
    elif dm["hi"] < 0:
        out.append("DECISION: b wins (pass_repair CI excludes 0)")
    else:
        out.append("DECISION: keep %s" % simpler)
    out.append("")
    return "\n".join(out)


def emit(text, out_path):
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv and argv[0] == "ab":
            p = argparse.ArgumentParser(prog="report.py ab")
            p.add_argument("--a", required=True)
            p.add_argument("--b", required=True)
            p.add_argument("--simpler", required=True, choices=["a", "b"])
            p.add_argument("--out")
            args = p.parse_args(argv[1:])
            emit(build_ab(args.a, args.b, args.simpler), args.out)
        else:
            p = argparse.ArgumentParser(prog="report.py")
            p.add_argument("--run", action="append", required=True, metavar="DIR")
            p.add_argument("--out")
            p.add_argument("--set", dest="only_set", choices=["dev", "hidden"])
            args = p.parse_args(argv)
            emit(build_report(args.run, args.only_set), args.out)
    except metrics.RecordError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
