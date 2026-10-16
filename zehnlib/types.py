"""zehnlib.types: moved verbatim from zehn.py (v0.3), no change of behaviour."""
from __future__ import annotations

import re


# ----------------------------------------------------------------------------
# Static type checker (SPEC section 3; replaces runtime-only E0306 detection)
# ----------------------------------------------------------------------------


class TVar:
    __slots__ = ("ref",)

    def __init__(self):
        self.ref = None


class TCon:
    __slots__ = ("name", "args")

    def __init__(self, name, args=()):
        self.name, self.args = name, tuple(args)


class TFn:
    __slots__ = ("params", "ret")

    def __init__(self, params, ret):
        self.params, self.ret = tuple(params), ret


INT, BOOL, TEXT, T_UNIT = TCon("Int"), TCon("Bool"), TCon("Text"), TCon("Unit")
PRIMS = {"Int", "Bool", "Text", "Unit"}
GENERIC_ARITY = {"List": 1, "Option": 1, "Result": 2, "Map": 2}


def prune(t):
    while isinstance(t, TVar) and t.ref is not None:
        t = t.ref
    return t


def show_t(t):
    t = prune(t)
    if isinstance(t, TVar):
        return "_"
    if isinstance(t, TFn):
        return "Fn(%s) -> %s" % (", ".join(show_t(p) for p in t.params), show_t(t.ret))
    if t.args:
        return "%s<%s>" % (t.name, ", ".join(show_t(a) for a in t.args))
    return t.name


def _occurs(v, t):
    t = prune(t)
    if t is v:
        return True
    if isinstance(t, TCon):
        return any(_occurs(v, a) for a in t.args)
    if isinstance(t, TFn):
        return any(_occurs(v, p) for p in t.params) or _occurs(v, t.ret)
    return False


def unify(a, b, trail=None):
    a, b = prune(a), prune(b)
    if a is b:
        return True
    if isinstance(a, TVar):
        if _occurs(a, b):
            return False
        a.ref = b
        if trail is not None:
            trail.append(a)
        return True
    if isinstance(b, TVar):
        return unify(b, a, trail)
    if isinstance(a, TCon) and isinstance(b, TCon):
        return (a.name == b.name and len(a.args) == len(b.args)
                and all(unify(x, y, trail) for x, y in zip(a.args, b.args)))
    if isinstance(a, TFn) and isinstance(b, TFn):
        return (len(a.params) == len(b.params)
                and all(unify(x, y, trail) for x, y in zip(a.params, b.params))
                and unify(a.ret, b.ret, trail))
    return False


def try_unify(a, b):
    """Like unify, but a failed attempt leaves no partial bindings behind."""
    trail = []
    ok = unify(a, b, trail)
    if not ok:
        for v in trail:
            v.ref = None
    return ok


_TY_TOK = re.compile(r"\s*(->|[A-Za-z_][A-Za-z0-9_]*|[<>(),])")


def parse_type_text(s, known, svars=None):
    """Type string -> type. `known` = user type names. `svars` (stdlib signatures only) maps
    single capital letters to type variables and enables `Fn(A) -> B`."""
    toks = _TY_TOK.findall(s)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take(x=None):
        t = peek()
        if t is None or (x is not None and t != x):
            raise ValueError("malformed type %r" % s)
        pos[0] += 1
        return t

    def many(close):
        ts = [one()]
        while peek() == ",":
            take(",")
            ts.append(one())
        take(close)
        return ts

    def one():
        t = take()
        if t == "(":
            return TCon("Tuple", many(")"))
        if svars is not None and t == "Fn":
            take("(")
            ps = [] if peek() == ")" else None
            if ps is None:
                ps = many(")")
            else:
                take(")")
            take("->")
            return TFn(ps, one())
        if svars is not None and len(t) == 1 and t.isupper():
            return svars.setdefault(t, TVar())
        if t in GENERIC_ARITY:
            take("<")
            args = many(">")
            if len(args) != GENERIC_ARITY[t]:
                raise ValueError("%s expects %d type argument(s)" % (t, GENERIC_ARITY[t]))
            return TCon(t, args)
        if t in PRIMS or t in known:
            return TCon(t)
        raise ValueError("unknown type %r" % t)

    r = one()
    if pos[0] != len(toks):
        raise ValueError("malformed type %r" % s)
    return r


def instantiate(sig):
    """Fresh (param types, return type) for a stdlib signature string."""
    svars = {}
    # find the `)` that closes the parameter list
    depth, cut = 0, None
    for i, ch in enumerate(sig):
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0:
            cut = i
            break
    params_s, ret_s = sig[1:cut], sig[cut + 1:].split("->", 1)[1]
    params = []
    if params_s.strip():
        depth, cur, prev = 0, "", ""
        for ch in params_s:
            if ch in "(<":
                depth += 1
            elif ch in ")>" and not (ch == ">" and prev == "-"):
                depth -= 1
            prev = ch
            if ch == "," and depth == 0:
                params.append(cur)
                cur = ""
            else:
                cur += ch
        params.append(cur)
    return ([parse_type_text(p.strip(), (), svars) for p in params],
            parse_type_text(ret_s.strip(), (), svars))




def unify_probe(a, b):
    """Would a and b unify? (does not keep bindings for concrete types)"""
    a, b = prune(a), prune(b)
    if isinstance(a, TVar) or isinstance(b, TVar):
        return False
    return show_t(a) == show_t(b)
