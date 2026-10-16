"""zehn hash: fn#xxxx refs for patching."""
from __future__ import annotations

import json

from zehnlib.cli import command
from zehnlib.fmt import definition_refs
from zehnlib.parser import parse


@command("hash", "hash    <file> [--json]")
def hash_(argv):
    refs = definition_refs(parse(open(argv[0], encoding="utf-8").read()))
    if "--json" in argv:
        print(json.dumps([{k: v for k, v in r.items() if k != "hash"} for r in refs],
                         ensure_ascii=False, indent=2))
    else:
        for r in refs:
            print("%-14s %s" % (r["ref"], r["name"]))
    return 0
