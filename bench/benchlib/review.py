"""Bet 1 (docs/WINNING_ANGLES.md): can a reviewer find a planted defect? Item building, prompts, scoring.

An item is one program shown to a reviewer: the reference solution (kind `clean`) or the reference with one
planted defect (kind `mutated`). A mutant is kept only if it (1) survives the program's own check
(`tool_check` ok: for Zehn that runs the program's examples and contracts, for Python the visible examples) and
(2) fails at least one hidden test, so it is a real defect that the program's own examples do not show.
Arms: `zehn`, `python` (description + code), `python_examples` (python plus the visible examples as comments:
separates "has examples" from "is Zehn").
"""
from __future__ import annotations

import json
import os
import random
import re
import tempfile
from typing import Any, Dict, List, Optional

from . import adapters, mutate

ARMS = ("zehn", "python", "python_examples")
_SRC_LANG = {"zehn": "zehn", "python": "python", "python_examples": "python"}
_ADAPTER = {"zehn": "zehn", "python": "python_plain", "python_examples": "python_plain"}
_REF = {"zehn": "ref.zehn", "python": "ref.py", "python_examples": "ref.py"}

ZEHN_GUIDE = """\
Reading guide for Zehn (a small typed language). A function is `fn name(params) -> Type`, then clauses, then
`do ... end fn`. `intent` is a plain-language purpose. `requires P` is a precondition, `ensures P` a postcondition
(`out` is the return value). `example E` is an executable test that the program already passes. `uses [console]`
declares effects. `match x do case ... => ... end match` must cover all cases; `list.get(xs, i)` returns an Option
(`some(v)` / `none`). `/` rounds toward negative infinity. Everything after `do` is the body.
"""

SYSTEM = """\
You are a code reviewer. You get a task description and a program that is supposed to solve it. Either the
program is correct, or it contains exactly ONE small defect (a wrong operator, an off-by-one, a flipped
condition, a wrong constant). About half of the programs you are shown are defective. You cannot run anything.
Reply with ONE line of JSON and nothing else:
{"verdict": "defect" or "correct", "line": <line number of the defect, or null>, "why": "<one short sentence>"}
"""


def visible_examples_comment(task: Dict[str, Any]) -> str:
    lines = ["# Visible examples (the program already passes these):"]
    for ex in task.get("visible_examples", []):
        args = ", ".join(json.dumps(a) for a in ex["args"])
        line = "#   %s(%s) == %s" % (task["entry"], args, json.dumps(ex["expect"]))
        if ex.get("stdout"):
            line += "   prints %s" % json.dumps(ex["stdout"])
        lines.append(line)
    return "\n".join(lines) + "\n"


def view_of(arm: str, task: Dict[str, Any], source: str) -> Dict[str, Any]:
    """The text the reviewer sees and the offset between source lines and shown lines."""
    if arm == "python_examples":
        head = visible_examples_comment(task)
        return {"code": head + source, "offset": head.count("\n")}
    return {"code": source, "offset": 0}


def numbered(code: str) -> str:
    return "\n".join("%3d  %s" % (i + 1, ln) for i, ln in enumerate(code.rstrip("\n").split("\n")))


def task_text(task: Dict[str, Any]) -> str:
    params = ", ".join("%s: %s" % (p["name"], p["type"]) for p in task["params"])
    eff = ("Effects: " + ", ".join(task["effects"]) + "\n") if task["effects"] else ""
    return "Task: %s\n%s\nFunction: %s(%s) -> %s\n%s" % (
        task["title"], task["description"], task["entry"], params, task["returns"], eff)


def system_for(arm: str) -> str:
    return SYSTEM + ("\n" + ZEHN_GUIDE if arm == "zehn" else "")


def user_message(task: Dict[str, Any], code: str) -> str:
    return task_text(task) + "\nProgram:\n" + numbered(code) + "\n"


def parse_reply(text: str) -> Dict[str, Any]:
    """{"verdict": "defect"|"correct"|None, "line": int|None, "why": str}"""
    m = re.search(r"\{.*\}", text or "", re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            v = str(d.get("verdict", "")).strip().lower()
            ln = d.get("line")
            return {"verdict": v if v in ("defect", "correct") else None,
                    "line": ln if isinstance(ln, int) and not isinstance(ln, bool) else None,
                    "why": str(d.get("why", ""))[:300]}
        except (ValueError, AttributeError):
            pass
    low = (text or "").lower()
    if '"defect"' in low or "verdict: defect" in low:
        return {"verdict": "defect", "line": None, "why": ""}
    if '"correct"' in low or "verdict: correct" in low:
        return {"verdict": "correct", "line": None, "why": ""}
    return {"verdict": None, "line": None, "why": ""}


def score(item: Dict[str, Any], reply: Dict[str, Any]) -> Dict[str, Any]:
    v = reply["verdict"]
    mutated = item["kind"] == "mutated"
    correct = (v == "defect") if mutated else (v == "correct")
    located = bool(mutated and v == "defect" and reply["line"] is not None
                   and abs(reply["line"] - item["shown_line"]) <= 1)
    return {"correct": bool(v is not None and correct), "located": located, "answered": v is not None}


def _survives_and_fails(adapter, task, code, work) -> Optional[bool]:
    chk = adapter.tool_check(task, code, work)
    if not chk.get("ok"):
        return None                      # does not survive its own check
    res = adapter.run_hidden(task, code, task["_tests"], work)
    return res["passed"] < res["total"]


MAX_TESTED = 30
MAX_KEPT = 8


def _task_items(task, arms, seed, log) -> List[Dict[str, Any]]:
    rng = random.Random("%s:%s" % (seed, task["id"]))
    srcs: Dict[str, str] = {}
    for lang in {_SRC_LANG[a] for a in arms}:
        path = os.path.join(task["_dir"], _REF["zehn" if lang == "zehn" else "python"])
        if not os.path.exists(path):
            log("skip %s: missing ref" % task["id"])
            return []
        with open(path, encoding="utf-8") as f:
            srcs[lang] = f.read()
    good: Dict[str, List[Dict[str, Any]]] = {}
    with tempfile.TemporaryDirectory() as work:
        for lang in sorted(srcs):
            ad = adapters.get("zehn" if lang == "zehn" else "python_plain")
            cands = mutate.mutants(srcs[lang], lang)
            rng.shuffle(cands)
            kept: List[Dict[str, Any]] = []
            for m in cands[:MAX_TESTED]:            # a cap: some mutants loop until the run timeout
                if _survives_and_fails(ad, task, m["source"], work):
                    kept.append(m)
                    if len(kept) >= MAX_KEPT:
                        break
            good[lang] = kept
    empty = [l for l in good if not good[l]]
    if empty:
        log("skip %s: no surviving defect in %s" % (task["id"], empty))
        return []
    picked: Dict[str, Dict[str, Any]] = {}
    for lang in (["zehn"] if "zehn" in good else []) + [l for l in sorted(good) if l != "zehn"]:
        pool = good[lang]
        if picked:
            ref_cls = next(iter(picked.values()))["cls"]
            pool = [m for m in pool if m["cls"] == ref_cls] or pool
        picked[lang] = rng.choice(pool)
    items: List[Dict[str, Any]] = []
    for arm in arms:
        m = picked[_SRC_LANG[arm]]
        for kind, source in (("mutated", m["source"]), ("clean", srcs[_SRC_LANG[arm]])):
            view = view_of(arm, task, source)
            items.append({
                "item_id": "%s:%s:%s" % (task["id"], arm, kind), "task_id": task["id"],
                "category": task["category"], "arm": arm, "kind": kind, "code": view["code"],
                "mutation": ({"cls": m["cls"], "op": m["op"], "line": m["line"]} if kind == "mutated" else None),
                "shown_line": (m["line"] + view["offset"]) if kind == "mutated" else None})
    log("ok %s: %d surviving defects (%s)" % (task["id"], sum(len(v) for v in good.values()),
                                              ", ".join("%s %d" % (l, len(v)) for l, v in sorted(good.items()))))
    return items


def build_items(tasks: List[Dict[str, Any]], arms=ARMS, seed: int = 1234, log=lambda s: None,
                workers: int = 8) -> List[Dict[str, Any]]:
    """For every task that has a surviving real defect in every arm: one mutated and one clean item per arm.
    The zehn mutant is drawn first; the python arms prefer a mutant of the same class (paired design)."""
    from concurrent.futures import ThreadPoolExecutor
    ordered = sorted(tasks, key=lambda t: t["id"])
    with ThreadPoolExecutor(max_workers=workers) as ex:
        parts = list(ex.map(lambda t: _task_items(t, arms, seed, log), ordered))
    return [i for part in parts for i in part]
