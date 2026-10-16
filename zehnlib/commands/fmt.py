"""zehn fmt: print, check or rewrite the canonical form."""
from __future__ import annotations

import sys

from zehnlib import dialect
from zehnlib.cli import command, dialect_opts
from zehnlib.fmt import format_program
from zehnlib.parser import parse


@command("fmt", "fmt     <file> [--write | --check] [--dialect name=value]...")
def fmt(argv):
    path, write, check = argv[0], "--write" in argv, "--check" in argv
    dia = dialect_opts(argv)
    src = open(path, encoding="utf-8").read()
    with dialect.using(dia):
        canon = format_program(parse(src))
    if check:
        if canon != src:
            print("not canonical: %s" % path)
            return 1
        return 0
    if write:
        if canon != src:
            open(path, "w", encoding="utf-8").write(canon)
        return 0
    sys.stdout.write(canon)
    return 0
