#!/usr/bin/env python3
"""Zehn benchmark CLI: list | verify-refs | run | replay | status | doctor.  Stdlib only, Python 3.9+."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import threading
from typing import Any, Dict, List, Optional, Set, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from benchlib import adapters, loop, models, schema, store  # noqa: E402
from benchlib.models import scheduler  # noqa: E402

PROJECT_ROOT = os.path.dirname(_HERE)
DEFAULT_TASKS = os.path.join(_HERE, "tasks")
DEFAULT_OUT = os.path.join(_HERE, "results")
DEFAULT_LIMITS = os.path.join(_HERE, "limits.json")


def _split(values: Optional[List[str]]) -> List[str]:
    out: List[str] = []
    for v in values or []:
        out += [x.strip() for x in v.split(",") if x.strip()]
    return out


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--lang", action="append", help="language adapter(s); repeatable or comma list (default: zehn)")
    p.add_argument("--tasks-dir", action="append", help="task root; repeatable (default: bench/tasks)")
    p.add_argument("--only", action="append", help="task ids, comma list")


def _add_run(p: argparse.ArgumentParser) -> None:
    p.add_argument("--repeats", type=int, default=5)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--max-rounds", type=int, default=5)
    p.add_argument("--variant", default="default", help="k=v[,k=v] (default: default)")
    p.add_argument("--set-label", choices=("dev", "hidden"), default="dev")
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--run-id")
    p.add_argument("--force", action="store_true", help="overwrite an existing run directory of an API run")
    p.add_argument("--resume", action="store_true",
                   help="keep the run directory and skip every attempt that already has a record")
    p.add_argument("--seed", type=int, default=1234, help="seed of the work order (default 1234)")
    p.add_argument("--limit-margin", type=float, default=0.9,
                   help="stay inside this fraction of each rate limit (default 0.9)")
    p.add_argument("--expected-output-tokens", type=int, default=1500,
                   help="output tokens assumed per call when budgeting tokens per minute (default 1500)")
    p.add_argument("--max-output-tokens", type=int, default=8192,
                   help="output limit sent to gemini:/openai: models (default 8192)")
    p.add_argument("--rpm", type=int, help="override requests per minute per key")
    p.add_argument("--tpm", type=int, help="override tokens per minute per key")
    p.add_argument("--rpd", type=int, help="override requests per day per key")
    p.add_argument("--limits-file", default=DEFAULT_LIMITS, help="limits table (default bench/limits.json)")
    p.add_argument("--time-budget-minutes", type=float,
                   help="stop starting new runs after N minutes, finish the running ones, save, exit 0")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="run.py", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add_common(sub.add_parser("list", help="list the tasks"))
    _add_common(sub.add_parser("verify-refs", help="check every ref.* and start.* against its adapter"))
    r = sub.add_parser("run", help="run models against tasks")
    _add_common(r)
    _add_run(r)
    r.add_argument("--models", action="append", required=True,
                   help="stub:perfect | stub:broken_then_fixed | stub:never_valid | anthropic:<model-id> | "
                        "gemini:<model-id> | openai:<model-id>")
    r.add_argument("--yes", action="store_true", help="required for every remote model (anthropic: costs money, "
                                                      "gemini:/openai: use your quota)")
    r.add_argument("--dry-run", action="store_true", help="print run and API-call counts, then exit")
    st = sub.add_parser("status", help="done / remaining of a run, without calling any model")
    _add_common(st)
    st.add_argument("--run-id", required=True)
    st.add_argument("--out", default=DEFAULT_OUT)
    st.add_argument("--models", action="append", help="model spec (default: the one in the run's meta.json)")
    st.add_argument("--repeats", type=int, default=5)
    st.add_argument("--variant", default="default")
    st.add_argument("--seed", type=int, default=1234)
    dr = sub.add_parser("doctor", help="check that the language tools exist; print their versions")
    dr.add_argument("--lang", action="append", help="language adapter(s); repeatable or comma list")
    rp = sub.add_parser("replay", help="run with stub:perfect (no network); CI uses it")
    _add_common(rp)
    _add_run(rp)
    return ap


def _langs(args: argparse.Namespace) -> List[Any]:
    names = _split(args.lang) or ["zehn"]
    out = []
    for n in names:
        if n not in adapters.REGISTRY:
            raise SystemExit("unknown language %r (have: %s)" % (n, ", ".join(sorted(adapters.REGISTRY))))
        out.append(adapters.get(n))
    return out


def _tasks(args: argparse.Namespace) -> List[Dict[str, Any]]:
    try:
        return schema.load_tasks(args.tasks_dir or [DEFAULT_TASKS], _split(args.only) or None)
    except schema.TaskError as ex:
        raise SystemExit("task error: %s" % ex)


def _read(task: Dict[str, Any], name: str) -> Optional[str]:
    path = os.path.join(task["_dir"], name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def cmd_list(args: argparse.Namespace) -> int:
    for t in _tasks(args):
        print("%-14s %-7s L%d %-5s %s" % (t["id"], t["category"], t["level"], t["kind"], t["title"]))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    tasks, langs = _tasks(args), _langs(args)
    bad = 0
    for ad in langs:
        ok, why = ad.available()
        if not ok:
            print("SKIP %s: %s" % (ad.name, why))
    for t in tasks:
        for ad in langs:
            if not ad.available()[0]:
                continue
            ref = _read(t, "ref" + ad.ext)
            if ref is None:
                print("SKIP %s %s: no ref%s" % (t["id"], ad.name, ad.ext))
                continue
            problems: List[str] = []
            with tempfile.TemporaryDirectory(prefix="zbench_") as work:
                chk = ad.tool_check(t, ref, work)
                if not chk["ok"]:
                    problems.append("ref fails tool_check: %s" % [d["code"] + ":" + d["message"] for d in chk["diagnostics"]][:3])
                res = ad.run_hidden(t, ref, t["_tests"], work)
                if res["passed"] != res["total"]:
                    problems.append("ref passes %d/%d hidden tests: %s" % (res["passed"], res["total"], res["failures"][:2]))
                if t["kind"] == "edit":
                    start = _read(t, "start" + ad.ext)
                    if start is None:
                        problems.append("edit task without start%s" % ad.ext)
                    else:
                        chk = ad.tool_check(t, start, work)
                        if not chk["ok"]:
                            problems.append("start fails tool_check: %s" % [d["code"] for d in chk["diagnostics"]][:3])
                        res2 = ad.run_hidden(t, start, t["_tests"], work)
                        if res2["passed"] == res2["total"]:
                            problems.append("start already passes every hidden test")
            if problems:
                bad += 1
                print("FAIL %s %s: %s" % (t["id"], ad.name, "; ".join(problems)))
            else:
                print("OK   %s %s (%d/%d)" % (t["id"], ad.name, res["passed"], res["total"]))
    return 1 if bad else 0


_DOCTOR_TOOLS = {
    "python_strict": [("mypy", None), ("ruff", None)],
    "ts_strict": [("tsc", None), ("node", None)],
    "rust": [("cargo", ["cargo"]), ("rustc", ["rustc"])],
    "rust_strict": [("cargo", ["cargo"]), ("rustc", ["rustc"]), ("clippy", ["cargo", "clippy"]),
                    ("rustfmt", ["rustfmt"])],
}


def cmd_doctor(args: argparse.Namespace) -> int:
    langs = _langs(args)
    print("python %s" % sys.version.split()[0])
    bad = 0
    for ad in langs:
        ok, why = ad.available()
        if not ok:
            bad += 1
            print("MISSING %s: %s" % (ad.name, why))
            continue
        versions = []
        for name, cmd in _DOCTOR_TOOLS.get(ad.name, []):
            if cmd is None:
                resolve = getattr(ad, "tool_command", None)
                cmd = resolve(name) if resolve else None
                cmd = cmd or ([shutil.which(name)] if shutil.which(name) else None)
            versions.append("%s=%s" % (name, store.tool_version(cmd) if cmd else "?"))
        print("OK      %s%s" % (ad.name, (" (" + "; ".join(versions) + ")") if versions else ""))
    return 1 if bad else 0


def _plan(args: argparse.Namespace, tasks: List[Dict[str, Any]], langs: List[Any],
          specs: List[str]) -> List[Tuple[Dict[str, Any], Any, str, int]]:
    return list(loop.work_order(tasks, langs, specs, args.repeats, args.seed))


def _read_records_tolerant(path: str) -> List[Dict[str, Any]]:
    """Records of a run for reading only: an unfinished last line is ignored."""
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
    return out


def cmd_status(args: argparse.Namespace) -> int:
    run_dir = os.path.join(args.out, store.check_run_id(args.run_id))
    specs = _split(args.models)
    if not specs:
        try:
            with open(os.path.join(run_dir, "meta.json"), encoding="utf-8") as f:
                specs = list(json.load(f).get("models", []))
        except (OSError, ValueError):
            specs = []
    if not specs:
        raise SystemExit("no model known for this run: pass --models")
    tasks, langs = _tasks(args), _langs(args)
    recs = _read_records_tolerant(os.path.join(run_dir, "records.jsonl"))
    have = {loop.done_key(r) for r in recs if all(k in r for k in ("task_id", "lang", "variant", "model", "repeat"))}
    plan = _plan(args, tasks, langs, specs)
    per_lang: Dict[str, List[int]] = {ad.name: [0, 0] for ad in langs}
    done = 0
    planned_keys = set()
    for t, ad, spec, rep in plan:
        key = (t["id"], ad.name, args.variant, spec, rep)
        planned_keys.add(key)
        if key in have:
            done += 1
            per_lang[ad.name][0] += 1
        else:
            per_lang[ad.name][1] += 1
    remaining = len(plan) - done
    rounds = [len(r.get("rounds", [])) for r in recs
              if all(k in r for k in ("task_id", "lang", "variant", "model", "repeat")) and loop.done_key(r) in planned_keys]
    avg = (sum(rounds) / len(rounds)) if rounds else 2.0
    errored = sum(1 for r in recs if r.get("error"))
    print("run: %s" % args.run_id)
    print("models: %s" % ", ".join(specs))
    print("done: %d" % done)
    print("remaining: %d" % remaining)
    print("errored records: %d" % errored)
    for name in sorted(per_lang):
        print("  %-14s done=%d remaining=%d" % (name, per_lang[name][0], per_lang[name][1]))
    print("estimated remaining calls: %d (%.2f rounds per run, %s)"
          % (int(round(remaining * avg)), avg, "measured" if rounds else "assumed, no finished runs yet"))
    return 0


def _clock() -> scheduler.Clock:
    try:
        scale = float(os.environ.get("BENCH_TIME_SCALE", "1"))
    except ValueError:
        scale = 1.0
    return scheduler.Clock(scale)


def cmd_run(args: argparse.Namespace, replay: bool = False) -> int:
    specs = ["stub:perfect"] if replay else _split(args.models)
    api = [m for m in specs if models.is_api_model(m)]
    remote = [m for m in specs if models.is_remote_model(m)]
    if remote and len(specs) != 1:
        raise SystemExit("a run uses exactly one model when it uses gemini:/openai: (different models are "
                         "different runs with different --run-id)")
    tasks, langs = _tasks(args), _langs(args)
    try:
        pairs = loop.parse_variant(args.variant)
    except ValueError as ex:
        raise SystemExit(str(ex))
    n_runs = len(tasks) * len(langs) * len(specs) * args.repeats
    if not replay and args.dry_run:
        print("runs: %d (%d tasks x %d langs x %d models x %d repeats)"
              % (n_runs, len(tasks), len(langs), len(specs), args.repeats))
        print("worst-case API calls: %d (%d tasks x %d langs x %d API models x %d repeats x %d max rounds)"
              % (len(tasks) * len(langs) * len(api) * args.repeats * args.max_rounds,
                 len(tasks), len(langs), len(api), args.repeats, args.max_rounds))
        return 0
    if api and not getattr(args, "yes", False):
        raise SystemExit("remote models (anthropic:, gemini:, openai:) need --yes (anthropic: costs money, the "
                         "others use your quota); --dry-run counts the calls")
    for ad in langs:
        ok, why = ad.available()
        if not ok:
            raise SystemExit("language %s is not available: %s" % (ad.name, why))
    limits: Optional[Dict[str, int]] = None
    if remote:
        try:
            table = scheduler.load_limits(args.limits_file)
        except (OSError, ValueError) as ex:
            if not all(getattr(args, f) for f in ("rpm", "tpm", "rpd")):
                raise SystemExit("cannot read %s (%s): pass --rpm, --tpm and --rpd" % (args.limits_file, ex))
            table = {}
        try:
            limits = scheduler.resolve_limits(remote[0], table,
                                              {"rpm": args.rpm, "tpm": args.tpm, "rpd": args.rpd})
        except models.ModelError as ex:
            raise SystemExit("model error: %s" % ex)
    try:
        clients = {m: models.get_model(m, **({"max_output_tokens": args.max_output_tokens}
                                             if models.is_remote_model(m) else {})) for m in specs}
    except models.ModelError as ex:
        raise SystemExit("model error: %s" % ex)
    run_id = args.run_id or store.default_run_id()
    try:
        rs = store.RunStore(args.out, run_id, overwrite=bool(api == [] or args.force), resume=args.resume)
    except (FileExistsError, ValueError) as ex:
        raise SystemExit(str(ex))
    argv = sys.argv[1:]
    meta = store.build_meta(argv, PROJECT_ROOT, [c.name for c in clients.values()], langs,
                            {"run_id": run_id, "variant": args.variant, "set": args.set_label,
                             "repeats": args.repeats, "temperature": args.temperature,
                             "max_rounds": args.max_rounds, "seed": args.seed,
                             "tasks": [t["id"] for t in tasks]})
    if remote:
        meta["api_hosts"] = {remote[0]: clients[remote[0]].host}
        meta["limits_per_key"] = limits
        meta["max_output_tokens"] = args.max_output_tokens
    if args.resume and os.path.exists(rs.meta_path):
        try:
            with open(rs.meta_path, encoding="utf-8") as f:
                old = json.load(f)
            sessions = old.get("sessions") or [{k: old.get(k) for k in ("date_utc", "python", "tools")}]
        except (OSError, ValueError, AttributeError):
            sessions = []
        meta["sessions"] = sessions + [{k: meta.get(k) for k in ("date_utc", "python", "tools")}]
    rs.write_meta(meta)

    for ad in langs:
        setter = getattr(ad, "set_variant", None)
        if setter:
            setter(pairs)
    plan = _plan(args, tasks, langs, specs)
    have: Set[Tuple[str, str, str, str, int]] = set()
    if args.resume:
        have = {loop.done_key(r) for r in store.read_records(rs.records_path)}
    items = [it for it in plan if (it[0]["id"], it[1].name, args.variant, it[2], it[3]) not in have]
    if args.resume:
        print("resume: %d of %d attempts already recorded, %d to do" % (len(plan) - len(items), len(plan), len(items)))

    clock = _clock()
    print_lock = threading.Lock()

    def log(text: str) -> None:
        with print_lock:
            print(text, flush=True)

    skipped = 0

    def execute(item: Tuple[Dict[str, Any], Any, str, int], worker: Any) -> Optional[Dict[str, Any]]:
        t, ad, spec, rep = item
        ref = _read(t, "ref" + ad.ext)
        if ref is None:
            if not api:
                return None
            ref = ""   # real models never read it
        start = _read(t, "start" + ad.ext)
        client = worker if remote else clients[spec]
        return loop.run_one(ad, t, client, run_id=run_id, set_label=args.set_label,
                            variant=args.variant, repeat=rep, temperature=args.temperature,
                            max_rounds=args.max_rounds, ref_code=ref, start_code=start)

    written = [0]

    def on_record(rec: Optional[Dict[str, Any]]) -> None:
        if rec is None:
            return
        rs.append(rec)
        written[0] += 1
        log("%s %s %s #%d: accepted_round=%s first_try=%s final=%d/%d%s" % (
            rec["task_id"], rec["lang"], rec["model"], rec["repeat"], rec["accepted_round"],
            rec["first_try_pass"], rec["final_tests"]["passed"], rec["final_tests"]["total"],
            " ERROR " + rec["error"] if rec["error"] else ""))

    if remote:
        quota = scheduler.QuotaState(os.path.join(rs.dir, "quota_state.json"), clock)
        workers: List[Any] = scheduler.build_key_clients(clients[remote[0]], limits or {}, args.limit_margin,
                                                         args.expected_output_tokens, clock, quota, log)
        log("%d key(s): %s; limits per key rpm=%d tpm=%d rpd=%d, margin %.2f" % (
            len(workers), ", ".join(w.key_id for w in workers), limits["rpm"], limits["tpm"],
            limits["rpd"], args.limit_margin))
    else:
        workers = [object()]
    for it in items:
        if _read(it[0], "ref" + it[1].ext) is None and not api:
            skipped += 1
            print("SKIP %s %s: no ref%s (stub models need it)" % (it[0]["id"], it[1].name, it[1].ext),
                  file=sys.stderr)
    res = scheduler.run_pool(items, workers, execute, on_record, clock,
                             getattr(args, "time_budget_minutes", None), log)
    print("wrote %d record(s) to %s" % (written[0], rs.records_path))
    if res.fatal:
        print("FATAL: %s" % res.fatal, file=sys.stderr)
        print("The run was saved; fix the cause and continue with --resume.", file=sys.stderr)
        return 2
    remaining = len(res.remaining)
    if remaining and res.budget_reached:
        print("TIME_BUDGET_REACHED remaining=%d" % remaining)
    elif remaining:
        print("QUOTA_EXHAUSTED remaining=%d" % remaining)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "verify-refs":
        return cmd_verify(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "doctor":
        return cmd_doctor(args)
    if args.cmd == "replay":
        return cmd_run(args, replay=True)
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
