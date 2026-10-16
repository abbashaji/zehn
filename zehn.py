#!/usr/bin/env python3
"""Zehn v0.3 reference interpreter.

Parses Zehn source, runs static checks (names, arity, mutability, effects,
exhaustiveness), executes programs, and verifies requires / ensures / example.
Every diagnostic is a machine-readable dict (see SPEC.md section 9).

(Each subcommand lives in zehnlib/commands/; `zehn.py --help` prints the live list.)

Usage:
    zehn.py check   <file> [--json] [--strict] [--fuel N] [--max-depth N] [--dialect name=value]...
    zehn.py run     <file> <fn> '<json-array-of-args>' [--grant console,time.now] [--now N]
                    [--fuel N] [--max-depth N] [--dialect name=value]...
    zehn.py fmt     <file> [--write | --check] [--dialect name=value]...
    zehn.py hash    <file> [--json]
    zehn.py patch   <file> replace <ref> --with <file|-> [--write]
    zehn.py patch   <file> delete  <ref> [--write]
    zehn.py patch   <file> insert  --with <file|-> [--write]
    zehn.py lock    <file>
    zehn.py explain <code>
"""
from __future__ import annotations

import sys

from zehnlib.analysis import analyze, static_diags
from zehnlib.cli import main, to_value
from zehnlib.errors import DEFAULT_DEPTH, DEFAULT_FUEL, ZehnError, run_guarded
from zehnlib.fmt import definition_refs, format_program
from zehnlib.interp import Interp
from zehnlib.parser import parse
from zehnlib.stdlib import BUILTINS, SIGS
from zehnlib.types import instantiate
from zehnlib.values import FnRef, MapV, Rec, V, eq, show

if __name__ == "__main__":
    sys.exit(main(sys.argv))
