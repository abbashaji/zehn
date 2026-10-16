from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Cmd:
    op: str
    key: str
    n: int


def run_script(cmds: List[Cmd]) -> int:
    store: Dict[str, int] = {}
    for pos, cmd in enumerate(cmds, start=1):
        if cmd.op == "set":
            store[cmd.key] = cmd.n
        elif cmd.op == "add":
            store[cmd.key] = store.get(cmd.key, 0) + cmd.n
        elif cmd.op == "get":
            if cmd.key in store:
                print(f"{cmd.key} = {store[cmd.key]}")
            else:
                print(f"{cmd.key}: unset")
        elif cmd.op == "del":
            if cmd.key in store:
                del store[cmd.key]
            else:
                print(f"nothing to delete: {cmd.key}")
        elif cmd.op == "dump":
            if store:
                for key, value in store.items():
                    print(f"{key}={value}")
            else:
                print("(empty)")
        else:
            print(f"command {pos}: bad op {cmd.op}")
    return len(store)
