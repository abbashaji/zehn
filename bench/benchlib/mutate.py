"""Plant one small, realistic defect in a reference solution (Bet 1, docs/WINNING_ANGLES.md).

Line-level operators on function-body lines only (never on `example`/`requires`/`ensures`/`intent`
lines, signatures or comments, never inside a string literal). Pure functions of (source, language,
seed): the same input always gives the same mutants. Whether a mutant is a real defect (fails a hidden
test) and survives the program's own checks is decided by the caller, not here.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# (class, regex, replacement). Regexes run on a line whose string literals are masked.
COMMON: List[Tuple[str, str, str]] = [
    ("arith", r"(?<=\w|\)) \+ (?=\w|\()", " - "),
    ("arith", r"(?<=\w|\)) - (?=\w|\()", " + "),
    ("arith", r"(?<=\w|\)) \* (?=\w|\()", " + "),
    ("boundary", r" <= ", " < "),
    ("boundary", r" < ", " <= "),
    ("boundary", r" >= ", " > "),
    ("boundary", r" > ", " >= "),
    ("compare", r" == ", " != "),
    ("compare", r" != ", " == "),
    ("const", r"(?<![\w.\x00])(\d+)(?![\w.\x00])", None),        # n -> n + 1 (handled in code)
]
ZEHN: List[Tuple[str, str, str]] = COMMON + [
    ("logic", r" and ", " or "),
    ("logic", r" or ", " and "),
    ("logic", r"\btrue\b", "false"),
    ("logic", r"\bfalse\b", "true"),
    ("logic", r"\bnot ", ""),
]
PYTHON: List[Tuple[str, str, str]] = COMMON + [
    ("logic", r" and ", " or "),
    ("logic", r" or ", " and "),
    ("logic", r"\bTrue\b", "False"),
    ("logic", r"\bFalse\b", "True"),
    ("logic", r"\bnot ", ""),
    ("arith", r" \+= ", " -= "),
    ("arith", r" -= ", " += "),
]
RULES: Dict[str, List[Tuple[str, str, str]]] = {"zehn": ZEHN, "python": PYTHON}

_STR = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')


def _mask(line: str) -> Tuple[str, List[str]]:
    held: List[str] = []

    def keep(m):
        held.append(m.group(0))
        return "\x00%d\x00" % (len(held) - 1)
    return _STR.sub(keep, line), held


def _unmask(line: str, held: List[str]) -> str:
    return re.sub("\x00(\\d+)\x00", lambda m: held[int(m.group(1))], line)


def body_lines(source: str, lang: str) -> List[int]:
    """0-based indexes of the lines a mutation may touch."""
    lines = source.split("\n")
    out: List[int] = []
    if lang == "zehn":
        inside = False
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s == "do":
                inside = True
            elif s == "end fn":
                inside = False
            elif inside and s and not s.startswith("--"):
                out.append(i)
        return out
    in_def = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if ln.startswith("def "):
            in_def = True
            continue
        if ln and not ln.startswith((" ", "\t")):
            in_def = False
        if in_def and s and not s.startswith(("#", '"""', "@")):
            out.append(i)
    return out


def mutants(source: str, lang: str) -> List[Dict[str, object]]:
    """Every single-edit mutant: {"cls", "line" (1-based), "op", "source"}; order is deterministic."""
    rules = RULES[lang]
    lines = source.split("\n")
    result: List[Dict[str, object]] = []
    seen = set()
    for i in body_lines(source, lang):
        masked, held = _mask(lines[i])
        for cls, pat, rep in rules:
            for m in re.finditer(pat, masked):
                if cls == "const":
                    new = str(int(m.group(1)) + 1)
                    cand = masked[:m.start(1)] + new + masked[m.end(1):]
                    op = "%s -> %s" % (m.group(1), new)
                else:
                    cand = masked[:m.start()] + rep + masked[m.end():]
                    op = "%r -> %r" % (m.group(0).strip(), rep.strip())
                text = _unmask(cand, held)
                if text == lines[i]:
                    continue
                key = (i, text)
                if key in seen:
                    continue
                seen.add(key)
                out = lines[:i] + [text] + lines[i + 1:]
                result.append({"cls": cls, "line": i + 1, "op": op, "source": "\n".join(out)})
    return result
