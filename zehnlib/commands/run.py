"""zehn run: call one function with JSON arguments."""
from __future__ import annotations

import json

from zehnlib import dialect
from zehnlib.analysis import nesting_error, static_diags
from zehnlib.cli import _opt, command, dialect_opts, to_value, usage_error
from zehnlib.errors import DEFAULT_DEPTH, DEFAULT_FUEL, ZehnError, host_stack_error, run_guarded
from zehnlib.interp import Interp
from zehnlib.parser import parse
from zehnlib.types import TCon, parse_type_text
from zehnlib.values import Rec, Tup, V, show


def typed_value(j, t, prog):
    """JSON -> Zehn value, guided by the declared type `t` (a zehnlib.types type, or None when it
    is unknown). Identical to `to_value` except that a tuple type takes a JSON list of exactly its
    elements (TASK_07): a JSON list is only read as a tuple where the declared type says so, so
    every other argument is converted as before. Types are followed through List, Option, Result,
    records and constructor arguments."""
    def ty(text):
        try:
            return parse_type_text(text, prog.types)
        except ValueError:
            return None

    if isinstance(t, TCon):
        if t.name == "Tuple":
            if not isinstance(j, list) or len(j) != len(t.args):
                raise ZehnError("E0306", "expected a JSON list of %d element(s) for a tuple, got %s"
                                % (len(t.args), json.dumps(j, ensure_ascii=False)), "runtime",
                                blame="caller",
                                fix_hint="pass the elements of the tuple, in order, as a JSON list")
            return Tup(tuple(typed_value(x, a, prog) for x, a in zip(j, t.args)))
        if t.name == "List" and isinstance(j, list):
            return [typed_value(x, t.args[0], prog) for x in j]
        if isinstance(j, dict) and "$" in j:
            name, args = j["$"], j.get("args", [])
            if t.name in ("Option", "Result"):
                slots = {"some": t.args[:1], "ok": t.args[:1], "err": t.args[1:2]}.get(name, [])
            else:
                slots = [ty(a) for a in prog.variant_args.get(name, [])]
            return V(name, tuple(typed_value(a, slots[i] if i < len(slots) else None, prog)
                                 for i, a in enumerate(args)))
        if isinstance(j, dict) and t.name in prog.types and prog.types[t.name]["kind"] == "record":
            decl = dict(prog.types[t.name]["fields"])
            return Rec((k, typed_value(v, ty(decl[k]) if k in decl else None, prog))
                       for k, v in j.items())
    return to_value(j)


@command("run", "run     <file> <fn> '<json-array-of-args>' [--grant console,time.now] [--now N] "
                "[--fuel N] [--max-depth N] [--dialect name=value]...")
def run(argv):
    if len(argv) < 3:
        return usage_error()
    path, fname, args_json = argv[0], argv[1], argv[2]
    grant = [g for g in (_opt(argv, "--grant", "") or "").split(",") if g]
    now = _opt(argv, "--now")
    now = int(now) if now is not None else None
    fuel = int(_opt(argv, "--fuel", DEFAULT_FUEL))
    max_depth = int(_opt(argv, "--max-depth", DEFAULT_DEPTH))
    dia = dialect_opts(argv)
    src = open(path, encoding="utf-8").read()

    def go():
        prog = parse(src)
        errs = [d for d in static_diags(prog) if d["severity"] == "error"]
        if errs:
            print(json.dumps(errs, ensure_ascii=False, indent=2))
            return 1
        if fname not in prog.funcs:
            print(json.dumps({"code": "E0302", "message": "unknown function %r" % fname}))
            return 1
        it = Interp(prog, granted=grant, now=now, fuel=fuel, max_depth=max_depth)
        it.fresh_budget()
        decl = [parse_type_text(ptxt, prog.types) for _, ptxt in prog.funcs[fname].params]
        try:
            given = json.loads(args_json)
            out = it.call_fn(prog.funcs[fname],
                             [typed_value(a, decl[i] if i < len(decl) else None, prog)
                              for i, a in enumerate(given)])
        except RecursionError:
            raise host_stack_error()
        print(show(out))
        return 0

    try:
        with dialect.using(dia):
            return run_guarded(go, max_depth)
    except RecursionError:
        raise nesting_error()
    except ZehnError as z:
        print(json.dumps(z.diag, ensure_ascii=False, indent=2))
        return 1
