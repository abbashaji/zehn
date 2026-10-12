"""Hidden-test runner for the Zehn adapter. Run as a subprocess:

    python3 _zehn_runner.py <project_root> <program.zehn> <spec.json>

spec.json = {"entry": str, "console": bool, "cases": [{"args": [...], "expect": <json>, "stdout": str?}]}
It imports the project's `zehn` module and uses only parse, Interp, to_value and show. Prints one JSON
object: {"stage": "ok"|"parse"|"entry", "error": str|None,
         "results": [{"ok": bool, "got": str, "want": str, "error": str|None}]}.
Stdlib only, Python 3.9+."""
from __future__ import annotations

import io
import json
import sys
from typing import Any, Dict, List


def _norm(v: Any) -> Any:
    """Records compare by field, not by the order the program wrote them in."""
    if isinstance(v, dict):
        return type(v)((k, _norm(x)) for k, x in sorted(v.items()))
    if isinstance(v, list):
        return [_norm(x) for x in v]
    if hasattr(v, "name") and isinstance(getattr(v, "args", None), tuple):
        return type(v)(v.name, tuple(_norm(a) for a in v.args))
    return v


def _err_text(ex: BaseException) -> str:
    diag = getattr(ex, "diag", None)
    if isinstance(diag, dict):
        return json.dumps(diag, ensure_ascii=False)[:500]
    return ("%s: %s" % (type(ex).__name__, ex))[:500]


def main(argv: List[str]) -> int:
    root, path, spec_path = argv[1], argv[2], argv[3]
    sys.path.insert(0, root)
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
    import zehn  # type: ignore[import-not-found]
    from zehn import Interp, parse, show, to_value  # type: ignore[import-not-found]
    del zehn
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    with open(path, encoding="utf-8") as f:
        src = f.read()
    out: Dict[str, Any] = {"stage": "ok", "error": None, "results": []}
    try:
        prog = parse(src)
    except BaseException as ex:  # noqa: BLE001 - any parse failure is a scored failure
        out.update(stage="parse", error=_err_text(ex))
        print(json.dumps(out))
        return 0
    fn = prog.funcs.get(spec["entry"])
    if fn is None:
        out.update(stage="entry", error="no function named %r" % spec["entry"])
        print(json.dumps(out))
        return 0
    for case in spec["cases"]:
        res: Dict[str, Any] = {"ok": False, "got": "", "want": "", "error": None}
        try:
            res["want"] = show(_norm(to_value(case["expect"])))
            buf = io.StringIO()
            it = Interp(prog, granted=["console"] if spec["console"] else [], stdout=buf)
            value = it.invoke(fn, [to_value(a) for a in case["args"]])
            res["got"] = show(_norm(value))
            ok = res["got"] == res["want"]
            if spec["console"] and "stdout" in case and buf.getvalue() != case["stdout"]:
                ok = False
                res["error"] = "console output %r, wanted %r" % (buf.getvalue()[:200], case["stdout"][:200])
            res["ok"] = ok
        except BaseException as ex:  # noqa: BLE001 - a crash is a failed case, not a runner crash
            res["error"] = _err_text(ex)
        out["results"].append(res)
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
