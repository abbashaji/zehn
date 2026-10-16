"""zehnlib.lexer: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import json
import re
from zehnlib.errors import ZehnError


# ----------------------------------------------------------------------------
# Lexer
# ----------------------------------------------------------------------------

KEYWORDS = {
    "fn", "type", "let", "var", "return", "if", "then", "else", "end", "match", "case",
    "do", "intent", "uses", "requires", "ensures", "example", "implies", "and", "or",
    "not", "true", "false",
}

TOKEN_RE = re.compile(r'''
    (?P<ws>[ \t\r]+)
  | (?P<comment>--[^\n]*)
  | (?P<nl>\n)
  | (?P<int>\d+)
  | (?P<str>"(?:[^"\\\n]|\\.)*")
  | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op>\|>|=>|->|:=|==|!=|<=|>=|[-+*/%<>=(){}\[\],.:|?])
''', re.X)


def tokenize(src, comments=None):
    """Tokens are (kind, value, line, start, end). Comments go to `comments` if given."""
    toks, pos, line = [], 0, 1
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise ZehnError("E0101", "unexpected character %r" % src[pos], "lex",
                            location={"line": line})
        kind, text = m.lastgroup, m.group()
        s, pos = m.start(), m.end()
        if kind in ("ws", "comment"):
            if kind == "comment" and comments is not None:
                trailing = bool(toks) and toks[-1][0] != "NL"
                comments.append((line, text, trailing))
            continue
        if kind == "nl":
            if toks and toks[-1][0] != "NL":
                toks.append(("NL", "\n", line, s, pos))
            line += 1
            continue
        if kind == "int":
            toks.append(("INT", int(text), line, s, pos))
        elif kind == "str":
            toks.append(("STR", json.loads(text), line, s, pos))
        elif kind == "id":
            if text in KEYWORDS:
                toks.append(("KW", text, line, s, pos))
            elif text[0].isupper():
                toks.append(("TID", text, line, s, pos))
            else:
                toks.append(("ID", text, line, s, pos))
        else:
            toks.append(("OP", text, line, s, pos))
    if not toks or toks[-1][0] != "NL":
        toks.append(("NL", "\n", line, len(src), len(src)))
    toks.append(("EOF", None, line, len(src), len(src)))
    return toks
