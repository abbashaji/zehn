from __future__ import annotations

import json
import os

from . import stats

METRICS = [
    "pass_at_1",
    "pass_repair",
    "repair_rounds",
    "silent_bug_rate",
    "hallucination_rate",
    "total_tokens",
    "stability",
]

METRIC_LABELS = {
    "pass_at_1": "pass@1",
    "pass_repair": "pass_repair",
    "repair_rounds": "repair rounds",
    "silent_bug_rate": "silent-bug rate",
    "hallucination_rate": "hallucination rate",
    "total_tokens": "total tokens",
    "stability": "stability",
}

NAN = float("nan")


# ---------------------------------------------------------------- loading

class RecordError(Exception):
    pass


def load_run(path):
    """Read one run directory. Returns (meta, records).

    records come from <path>/records.jsonl (schema 1, one JSON object per
    line). meta is the optional <path>/meta.json (a dict) or {}.
    """
    rec_path = os.path.join(path, "records.jsonl")
    if not os.path.isfile(rec_path):
        raise RecordError("no records.jsonl in %s" % path)
    records = []
    with open(rec_path, encoding="utf-8") as fh:
        for no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError as exc:
                raise RecordError("%s line %d: invalid JSON (%s)" % (rec_path, no, exc))
            if not isinstance(rec, dict) or rec.get("schema") != 1:
                raise RecordError("%s line %d: not a schema 1 record" % (rec_path, no))
            records.append(rec)
    meta = {}
    meta_path = os.path.join(path, "meta.json")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as fh:
                loaded = json.load(fh)
        except ValueError as exc:
            raise RecordError("%s: invalid JSON (%s)" % (meta_path, exc))
        if isinstance(loaded, dict):
            meta = loaded
    return meta, records


def infer_max_rounds(records, metas=()):
    """max_rounds: from meta.json ('max_rounds') when present, else the most
    rounds any record used (at least 1)."""
    best = 0
    for meta in metas:
        v = meta.get("max_rounds")
        if isinstance(v, int) and v > best:
            best = v
    for rec in records:
        best = max(best, len(rec.get("rounds") or []))
    return max(best, 1)


# ---------------------------------------------------------- run-level values

def group_key(rec):
    return (rec["lang"], rec["variant"], rec["model"])


def matches(rec, spec):
    """spec 'python_strict' = lang python and variant strict; a bare language
    name ('zehn') matches every variant of that language."""
    lang, _, variant = spec.partition("_")
    if rec["lang"] == spec:
        return True
    return rec["lang"] == lang and variant != "" and rec["variant"] == variant


def run_pass1(rec):
    return 1.0 if rec["first_try_pass"] else 0.0


def run_pass_repair(rec):
    return 1.0 if (rec["accepted_round"] is not None and rec["final_pass"]) else 0.0


def run_repair_rounds(rec, max_rounds):
    if rec["accepted_round"] is None:
        return float(max_rounds - 1)
    return float(rec["accepted_round"] - 1)


def run_silent(rec):
    return 1.0 if (rec["accepted_round"] is not None and not rec["final_pass"]) else 0.0


def run_tokens(rec):
    return float(rec["total_in_tokens"] + rec["total_out_tokens"])


def run_halluc_parts(rec):
    """(unknown_names, diagnostics) summed over all rounds of one run."""
    unknown = 0
    diags = 0
    for rnd in rec.get("rounds") or []:
        unknown += rnd.get("unknown_names", 0)
        diags += len(rnd.get("diag_codes") or [])
    return (unknown, diags)


def _ratio_of_sums(pairs):
    num = 0
    den = 0
    for n_, d_ in pairs:
        num += n_
        den += d_
    if den == 0:
        return NAN
    return num / den


def _variance_by_task_model(records):
    """{(task, model): population variance of first_try_pass across repeats}"""
    cells = {}
    for rec in records:
        cells.setdefault((rec["task_id"], rec["model"]), []).append(run_pass1(rec))
    return {k: stats.variance(v) for k, v in cells.items()}


# ---------------------------------------------------------- group metrics

def summarize(records, max_rounds):
    """The seven metrics (plus counts) over a list of records, pooled over runs.

    pass@1, pass_repair, repair rounds, silent-bug rate, tokens are means over
    runs; hallucination rate is sum(unknown_names)/sum(diagnostics);
    stability is the mean over tasks of the variance of first_try_pass across
    repeats (variance within each (task, model) cell, averaged over models).
    """
    n = len(records)
    out = {
        "n_runs": n,
        "n_tasks": len(set(r["task_id"] for r in records)),
        "censored": sum(1 for r in records if r["accepted_round"] is None),
    }
    if n == 0:
        for m in METRICS:
            out[m] = NAN
        return out
    out["pass_at_1"] = stats.mean(run_pass1(r) for r in records)
    out["pass_repair"] = stats.mean(run_pass_repair(r) for r in records)
    out["repair_rounds"] = stats.mean(run_repair_rounds(r, max_rounds) for r in records)
    out["silent_bug_rate"] = stats.mean(run_silent(r) for r in records)
    out["hallucination_rate"] = _ratio_of_sums(run_halluc_parts(r) for r in records)
    out["total_tokens"] = stats.mean(run_tokens(r) for r in records)
    out["stability"] = stats.mean(task_series(records, "stability", max_rounds).values())
    return out


# ------------------------------------------------------ per-task series

def reducer(metric):
    """How per-task values of a metric are reduced to one number."""
    if metric == "hallucination_rate":
        return _ratio_of_sums
    return stats.mean


def task_series(records, metric, max_rounds):
    """{task_id: value}. Each task's value averages repeats first and models
    second (mean of per-model means). hallucination_rate gives (unknown,
    diagnostics) sums instead, reduced by ratio of sums. stability gives the
    mean over models of the across-repeat variance of first_try_pass."""
    if metric == "stability":
        var = _variance_by_task_model(records)
        per_task = {}
        for (task, _model), v in var.items():
            per_task.setdefault(task, []).append(v)
        return {t: stats.mean(v) for t, v in per_task.items()}
    if metric == "hallucination_rate":
        out = {}
        for rec in records:
            u, d = run_halluc_parts(rec)
            cur = out.get(rec["task_id"], (0, 0))
            out[rec["task_id"]] = (cur[0] + u, cur[1] + d)
        return out
    fn = {
        "pass_at_1": run_pass1,
        "pass_repair": run_pass_repair,
        "repair_rounds": lambda r: run_repair_rounds(r, max_rounds),
        "silent_bug_rate": run_silent,
        "total_tokens": run_tokens,
    }[metric]
    cells = {}
    for rec in records:
        cells.setdefault(rec["task_id"], {}).setdefault(rec["model"], []).append(fn(rec))
    return {
        t: stats.mean(stats.mean(v) for _m, v in sorted(models.items()))
        for t, models in cells.items()
    }


def min_repeats(records):
    """Smallest number of records in any (task, lang, variant, model) cell."""
    cells = {}
    for rec in records:
        k = (rec["task_id"],) + group_key(rec)
        cells[k] = cells.get(k, 0) + 1
    return min(cells.values()) if cells else 0


def paired(recs_a, recs_b, metric, max_rounds, how="diff",
           n=stats.DEFAULT_N, seed=stats.DEFAULT_SEED, alpha=stats.DEFAULT_ALPHA):
    """Paired comparison of one metric, resampling tasks.

    Returns dict(est, lo, hi, n_tasks, repeats, a, b) where a and b are the
    reduced point values on the common tasks and how is 'diff' (a - b) or
    'ratio' (a / b). Tasks missing on either side are left out.
    """
    sa = task_series(recs_a, metric, max_rounds)
    sb = task_series(recs_b, metric, max_rounds)
    tasks = sorted(set(sa) & set(sb))
    va = [sa[t] for t in tasks]
    vb = [sb[t] for t in tasks]
    red = reducer(metric)
    combine = stats.ratio if how == "ratio" else stats.diff
    est, lo, hi = stats.paired_bootstrap(va, vb, combine, red, n, seed, alpha)
    on = set(tasks)
    repeats = min_repeats([r for r in list(recs_a) + list(recs_b) if r["task_id"] in on])
    return {
        "est": est, "lo": lo, "hi": hi, "n_tasks": len(tasks), "repeats": repeats,
        "a": red(va) if va else NAN, "b": red(vb) if vb else NAN,
    }


# --------------------------------------------------------------- verdicts

MIN_TASKS = 150
MIN_REPEATS = 5


def verdict(h, lo, hi):
    """'supported' | 'refuted' | 'inconclusive' for hypothesis h (binding rules)."""
    if lo != lo or hi != hi:
        return "no data"
    if h == "H1":
        if lo >= 0.8:
            return "supported"
        if hi < 0.8:
            return "refuted"
    elif h in ("H2", "H3"):
        if hi < 0:
            return "supported"
        if lo >= 0:
            return "refuted"
    elif h == "H4":
        if hi <= 0:
            return "supported"
        if lo > 0:
            return "refuted"
    elif h == "H5":
        if lo > 0:
            return "supported"
        if hi <= 0:
            return "refuted"
    else:
        raise ValueError("unknown hypothesis %r" % h)
    return "inconclusive"


def is_underpowered(n_tasks, repeats):
    return n_tasks < MIN_TASKS or repeats < MIN_REPEATS


HYPOTHESES = [
    # id, metric, how, left, right, description
    ("H1", "pass_at_1", "ratio", "zehn", "python_plain", "pass@1 ratio zehn / python_plain (supported if CI lower >= 0.8)"),
    ("H2", "repair_rounds", "diff", "zehn", "python_strict", "repair rounds, zehn - python_strict"),
    ("H3", "silent_bug_rate", "diff", "zehn", "python_strict", "silent-bug rate, zehn - python_strict"),
    ("H4", "total_tokens", "diff", "zehn", "python_strict", "total tokens, zehn - python_strict"),
    ("H5", "pass_repair", "diff", "zehn", "rust_strict", "pass_repair, zehn - rust_strict"),
]


def evaluate_hypotheses(records, max_rounds, n=stats.DEFAULT_N, seed=stats.DEFAULT_SEED,
                        alpha=stats.DEFAULT_ALPHA):
    """List of dicts, one per hypothesis, in H1..H5 order."""
    out = []
    for hid, metric, how, left, right, desc in HYPOTHESES:
        ra = [r for r in records if matches(r, left)]
        rb = [r for r in records if matches(r, right)]
        row = {"id": hid, "metric": metric, "how": how, "left": left, "right": right, "desc": desc}
        res = paired(ra, rb, metric, max_rounds, how, n, seed, alpha) if ra and rb else None
        if res is None or res["n_tasks"] == 0:
            row.update(est=NAN, lo=NAN, hi=NAN, n_tasks=0, repeats=0,
                       verdict="no data", underpowered=False)
        else:
            v = verdict(hid, res["lo"], res["hi"])
            row.update(est=res["est"], lo=res["lo"], hi=res["hi"], n_tasks=res["n_tasks"],
                       repeats=res["repeats"], verdict=v,
                       underpowered=(v != "no data" and is_underpowered(res["n_tasks"], res["repeats"])))
        out.append(row)
    return out
