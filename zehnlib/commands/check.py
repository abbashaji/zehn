"""zehn check: types, effects, return paths, contracts, examples."""
from __future__ import annotations

import json

from zehnlib.analysis import analyze, fmt_diag
from zehnlib.cli import _opt, command, dialect_opts
from zehnlib.errors import DEFAULT_DEPTH, DEFAULT_FUEL, run_guarded
from zehnlib.fmt import definition_refs


@command("check", "check   <file> [--json] [--strict] [--fuel N] [--max-depth N] [--dialect name=value]...")
def check(argv):
    path, as_json, strict = argv[0], "--json" in argv, "--strict" in argv
    fuel = int(_opt(argv, "--fuel", DEFAULT_FUEL))
    max_depth = int(_opt(argv, "--max-depth", DEFAULT_DEPTH))
    dia = dialect_opts(argv)
    src = open(path, encoding="utf-8").read()
    prog, diags, examples = run_guarded(
        lambda: analyze(src, strict, path, fuel, max_depth, guard=False, dialect=dia), max_depth)
    failed = [x for x in examples if x["status"] == "fail"]
    n_err = sum(1 for d in diags if d["severity"] == "error") + len(failed)
    passed = sum(1 for x in examples if x["status"] == "pass")
    if as_json:
        defs = [{k: v for k, v in r.items() if k != "hash"} for r in definition_refs(prog)] if prog else []
        print(json.dumps({"schema": 1, "ok": n_err == 0, "diagnostics": diags, "definitions": defs,
                          "examples": {"passed": passed, "failed": len(failed), "results": examples}},
                         ensure_ascii=False, indent=2))
    else:
        for d in diags:
            print(fmt_diag(d))
        for x in failed:
            print(fmt_diag(x["diag"]))
        print("%s: %d error(s), %d example(s) passed, %d failed" %
              ("FAIL" if n_err else "OK", n_err, passed, len(failed)))
    return 1 if n_err else 0
