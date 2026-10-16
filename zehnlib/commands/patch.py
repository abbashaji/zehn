"""zehn patch: replace, delete or insert one definition addressed by its content hash."""
from __future__ import annotations

import json
import sys

from zehnlib.analysis import analyze, fmt_diag
from zehnlib.cli import _opt, command, usage_error
from zehnlib.errors import ZehnError
from zehnlib.fmt import Fmt, definition_refs
from zehnlib.parser import parse


def _perr(code, msg, **extra):
    d = {"code": code, "severity": "error", "phase": "patch", "message": msg}
    d.update(extra)
    return d


def cmd_patch(path, argv):
    """zehn patch <file> replace <ref> --with <file|->   |   delete <ref>   |   insert --with <file|->
    Dry run prints the patched source; --write applies it only when the result has no errors."""
    verb = argv[0] if argv else ""
    src = open(path, encoding="utf-8").read()
    prog = parse(src)
    chunks = [list(c) for c in Fmt(prog, comments=True).chunks()]
    refs = definition_refs(prog)
    by_pos = [i for i, c in enumerate(chunks) if c[0] != "tail"]
    ref_of = {pos: r for pos, r in zip(by_pos, refs)}
    new_text = None
    if verb in ("replace", "insert"):
        w = _opt(argv, "--with")
        if w is None:
            print(json.dumps(_perr("E0703", "%s needs --with <file|->" % verb), ensure_ascii=False))
            return 1
        new_src = sys.stdin.read() if w == "-" else open(w, encoding="utf-8").read()
        try:
            np_ = parse(new_src)
        except ZehnError as z:
            print(json.dumps(z.diag, ensure_ascii=False, indent=2))
            return 1
        if len(np_.order) != 1:
            print(json.dumps(_perr("E0703", "--with must contain exactly one definition, found %d"
                                   % len(np_.order)), ensure_ascii=False))
            return 1
        new_text = Fmt(np_, comments=True).chunks()[0]
    target = None
    if verb in ("replace", "delete"):
        if len(argv) < 2 or "#" not in argv[1]:
            print(json.dumps(_perr("E0701", "%s needs a ref like fn#a3f9" % verb), ensure_ascii=False))
            return 1
        kind, _, h = argv[1].partition("#")
        hits = [p for p, r in ref_of.items() if r["kind"] == kind and r["hash"].startswith(h.lower())]
        have = [r["ref"] for r in refs]
        if not hits or len(h) < 4:
            print(json.dumps(_perr("E0701", "no definition matches %s; it may have changed since you "
                                   "read the file" % argv[1], current_refs=have,
                                   fix_hint="run `zehn hash` and use a current ref"),
                             ensure_ascii=False, indent=2))
            return 1
        if len(hits) > 1:
            print(json.dumps(_perr("E0702", "ref %s is ambiguous" % argv[1],
                                   candidates=[ref_of[p]["ref"] for p in hits],
                                   fix_hint="use a longer hash prefix"), ensure_ascii=False, indent=2))
            return 1
        target = hits[0]
        if verb == "replace" and new_text[0] != kind:
            print(json.dumps(_perr("E0703", "cannot replace a %s with a %s" % (kind, new_text[0])),
                             ensure_ascii=False))
            return 1
    if verb == "replace":
        chunks[target] = list(new_text)
    elif verb == "delete":
        del chunks[target]
    elif verb == "insert":
        at = by_pos[-1] + 1 if by_pos else 0
        chunks.insert(at, list(new_text))
    else:
        return usage_error()
    out = "\n\n".join(c[2] for c in chunks) + "\n"
    prog2, diags, examples = analyze(out, False, None)
    failed = [x for x in examples if x["status"] == "fail"]
    errors = [d for d in diags if d["severity"] == "error"] + [x["diag"] for x in failed]
    if "--write" in argv and not errors:
        open(path, "w", encoding="utf-8").write(out)
        refs2 = definition_refs(prog2)
        print("patched %s; refs now: %s" % (path, ", ".join(r["ref"] for r in refs2)))
        return 0
    if "--write" not in argv:
        sys.stdout.write(out)
    for d in errors:
        sys.stderr.write(fmt_diag(d) + "\n")
    if errors and "--write" in argv:
        sys.stderr.write("not written: the patched program has %d error(s)\n" % len(errors))
    return 1 if errors else 0


@command("patch", "patch   <file> replace <ref> --with <file|-> [--write]\n"
                  "patch   <file> delete  <ref> [--write]\n"
                  "patch   <file> insert  --with <file|-> [--write]")
def patch(argv):
    if len(argv) < 2:
        return usage_error()
    return cmd_patch(argv[0], argv[1:])
