"""The model-in-the-loop runner: prompt, answer, tool feedback, repair, hidden tests, one record per run."""
from __future__ import annotations

import json
import random
import re
import tempfile
import time
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

from .models import RunAborted
from .schema import RECORD_SCHEMA_VERSION

FIX_REQUEST = "Fix the program and reply with the complete program in one code block."
_FENCE = re.compile(r"^[ \t]*```[^\n]*\n(.*?)^[ \t]*```[ \t]*$", re.MULTILINE | re.DOTALL)


def parse_variant(text: str) -> List[Tuple[str, str]]:
    """`default` -> []; `k=v[,k=v]` -> [(k, v), ...]. Raises ValueError on a malformed pair."""
    text = (text or "default").strip()
    if text == "default":
        return []
    pairs = []
    for part in text.split(","):
        k, eq, v = part.partition("=")
        if not eq or not k.strip() or not v.strip():
            raise ValueError("bad variant %r: expected k=v[,k=v]" % text)
        pairs.append((k.strip(), v.strip()))
    return pairs


def extract_code(text: str) -> Optional[str]:
    """The last fenced code block of a reply (None if there is none)."""
    blocks = _FENCE.findall(text)
    if not blocks:
        return None
    code = blocks[-1]
    return code if code.endswith("\n") else code + "\n"


def signature(task: Dict[str, Any]) -> str:
    return "%s(%s) -> %s" % (task["entry"], ", ".join("%s: %s" % (p["name"], p["type"]) for p in task["params"]),
                             task["returns"])


def task_prompt(task: Dict[str, Any], start_code: Optional[str], lang_ext: str) -> str:
    """Turn 1. Never includes `notes` or any hidden test."""
    lines = [task["title"], "", task["description"], "",
             "Function to implement (types in Zehn notation): `%s`" % signature(task)]
    if task["types"]:
        lines += ["", "Record types:"]
        for r in task["types"]:
            lines.append("- %s = { %s }" % (r["name"], ", ".join("%s: %s" % (f["name"], f["type"]) for f in r["fields"])))
    if "console" in task["effects"]:
        lines += ["", "This function prints to the console; the exact printed text is part of the tests."]
    lines += ["", "Examples (arguments -> expected result, as JSON):"]
    for ex in task["visible_examples"]:
        lines.append("- %s -> %s" % (json.dumps(ex["args"]), json.dumps(ex["expect"])))
    if task["kind"] == "edit" and start_code is not None:
        lines += ["", "Start from this program and change it so it does what is described:", "",
                  "```%s" % lang_ext.lstrip("."), start_code.rstrip("\n"), "```"]
    lines += ["", "Reply with the complete program in one code block."]
    return "\n".join(lines)


def feedback_prompt(check: Dict[str, Any]) -> str:
    return json.dumps(check, ensure_ascii=False, indent=2) + "\n\n" + FIX_REQUEST


def _unknown_count(check: Dict[str, Any]) -> int:
    return sum(1 for d in check["diagnostics"] if d.get("unknown_name"))


def run_one(adapter: Any, task: Dict[str, Any], model: Any, *, run_id: str, set_label: str,
            variant: str, repeat: int, temperature: float, max_rounds: int,
            ref_code: str, start_code: Optional[str] = None) -> Dict[str, Any]:
    """One (task, language, model, repeat) run. Returns a schema-1 record; never raises for model or
    tool trouble (that goes to `error`)."""
    tests = task["_tests"]
    total = len(tests)
    system = adapter.system_prompt(task)
    messages: List[Dict[str, str]] = [{"role": "user", "content": task_prompt(task, start_code, adapter.ext)}]
    rounds: List[Dict[str, Any]] = []
    attempts: List[str] = []
    first: Optional[Dict[str, Any]] = None
    accepted: Optional[int] = None
    error: Optional[str] = None
    t0 = time.time()
    in_tot = out_tot = 0
    with tempfile.TemporaryDirectory(prefix="zbench_") as work:
        for i in range(1, max_rounds + 1):
            try:
                reply = model.complete(system, messages, temperature,
                                       {"task": task, "lang": adapter.name, "ext": adapter.ext,
                                        "round": i, "ref_code": ref_code})
            except RunAborted:
                raise   # the scheduler requeues the whole run; nothing partial is recorded
            except Exception as ex:  # noqa: BLE001 - recorded, the run ends here
                error = "%s: %s" % (type(ex).__name__, ex)
                break
            in_tot += reply["in_tokens"]
            out_tot += reply["out_tokens"]
            code = extract_code(reply["text"])
            if code is None:
                attempts.append("")
                if reply.get("truncated"):
                    diag = {"code": "TRUNCATED", "line": None, "unknown_name": False, "raw": "",
                            "message": "the reply was cut off by the output limit before a complete code "
                                       "block; answer with a shorter program and no extra text"}
                else:
                    diag = {"code": "NOCODE", "message": "the reply contained no fenced code block",
                            "line": None, "unknown_name": False, "raw": ""}
                check = {"ok": False, "tool_ms": 0, "diagnostics": [diag]}
            else:
                attempts.append(code)
                try:
                    check = adapter.tool_check(task, code, work)
                except Exception as ex:  # noqa: BLE001
                    error = "tool_check crashed: %s: %s" % (type(ex).__name__, ex)
                    break
            rounds.append({"i": i, "tool_ok": bool(check["ok"]),
                           "diag_codes": [d["code"] for d in check["diagnostics"]],
                           "unknown_names": _unknown_count(check),
                           "in_tokens": reply["in_tokens"], "out_tokens": reply["out_tokens"]})
            if i == 1:
                first = _hidden(adapter, task, attempts[0], tests, work)
            if check["ok"]:
                accepted = i
                break
            messages.append({"role": "assistant", "content": reply["text"]})
            messages.append({"role": "user", "content": feedback_prompt(check)})
        final: Dict[str, Any] = {"passed": 0, "total": total}
        if attempts:
            if len(attempts) == 1 and first is not None:
                final = first
            else:
                final = _hidden(adapter, task, attempts[-1], tests, work)
    first_pass = bool(first and first["passed"] == total)
    return {
        "schema": RECORD_SCHEMA_VERSION, "run_id": run_id, "set": set_label, "task_id": task["id"],
        "category": task["category"], "kind": task["kind"], "lang": adapter.name, "variant": variant,
        "model": model.name, "repeat": repeat, "temperature": temperature, "rounds": rounds,
        "accepted_round": accepted, "first_try_pass": first_pass,
        "final_pass": bool(attempts) and final["passed"] == total,
        "final_tests": {"passed": final["passed"], "total": total},
        "total_in_tokens": in_tot, "total_out_tokens": out_tot,
        "wall_ms": int((time.time() - t0) * 1000), "error": error,
    }


def work_order(tasks: Sequence[Dict[str, Any]], langs: Sequence[Any], model_specs: Sequence[str],
               repeats: int, seed: int) -> Iterator[Tuple[Dict[str, Any], Any, str, int]]:
    """The run's work list, repeat-major: all of repeat 1, then repeat 2, ... Inside a repeat the tasks
    are interleaved round-robin across categories (each category shuffled with the seed) and every task
    is followed by all its (language, model) combinations, languages in a seeded order.

    Proven property: in any prefix of the list, the numbers of items per language differ by at most 1
    (a prefix is whole task blocks, where every language appears equally often, plus part of one block,
    where each language appears at most once more); while every category still has unscheduled tasks
    the numbers of tasks started per category differ by at most 1. A repeat's order depends only on
    (seed, repeat, task set), not on how many repeats were asked for."""
    for rep in range(1, repeats + 1):
        rng = random.Random("%d:%d" % (seed, rep))
        by_cat: Dict[str, List[Dict[str, Any]]] = {}
        for t in sorted(tasks, key=lambda x: x["id"]):
            by_cat.setdefault(t["category"], []).append(t)
        for group in by_cat.values():
            rng.shuffle(group)
        cats = sorted(by_cat)
        rng.shuffle(cats)
        order: List[Dict[str, Any]] = []
        while any(by_cat[c] for c in cats):
            for c in cats:
                if by_cat[c]:
                    order.append(by_cat[c].pop())
        for t in order:
            ls = list(langs)
            rng.shuffle(ls)
            for ad in ls:
                for spec in model_specs:
                    yield t, ad, spec, rep


def done_key(rec: Dict[str, Any]) -> Tuple[str, str, str, str, int]:
    return (rec["task_id"], rec["lang"], rec["variant"], rec["model"], rec["repeat"])


def _hidden(adapter: Any, task: Dict[str, Any], code: str, tests: List[Dict[str, Any]], work: str) -> Dict[str, Any]:
    if not code.strip():
        return {"passed": 0, "total": len(tests), "failures": [], "ms": 0}
    try:
        return adapter.run_hidden(task, code, tests, work)
    except Exception:  # noqa: BLE001 - an adapter crash scores the attempt as failed
        return {"passed": 0, "total": len(tests), "failures": [], "ms": 0}
