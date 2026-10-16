"""zehn lock: record the current intents so later drift can be detected (W0201)."""
from __future__ import annotations

import json

from zehnlib.analysis import lock_path
from zehnlib.cli import command
from zehnlib.fmt import lock_data
from zehnlib.parser import parse


@command("lock", "lock    <file>")
def lock(argv):
    path = argv[0]
    prog = parse(open(path, encoding="utf-8").read())
    with open(lock_path(path), "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "functions": lock_data(prog)}, fh, ensure_ascii=False, indent=2,
                  sort_keys=True)
        fh.write("\n")
    print("locked %d intent(s) in %s" % (len(lock_data(prog)), lock_path(path)))
    return 0
