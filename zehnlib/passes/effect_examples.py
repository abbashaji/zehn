"""Dialect flag `effect_examples` (ADR-0019): examples of effectful functions with a mock handler.

    example print_numbered(["a", "b"]) == 2 with console = mock [] prints ["1. a", "2. b"]
    example stamp_plus(5) == 105 with time.now = mock [100]

`off` (default) is v0.3. Under `mock` an example may carry, after its expression, any number of
`with <effect> = mock [<results>]` clauses and one `prints [<texts>]` clause.

This module owns the flag, the `zehn explain` texts of E0605 to E0607, the coverage check (E0605)
and the strict rule, plus two helpers the type checker and the interpreter share. The other
pieces sit where they belong: parsing in parser.py, printing in fmt.py, E0602 relief in
checker.py, mock typing (E0607) in typecheck.py, mock running (E0606) in interp.py.

The coverage check (E0605) is the static pass `effect_examples` at order 420: it runs after the
names, types, returns, recursion and int_ops passes, and reports nothing unless the flag is `mock`
(merge of TASK 06a: it ran at the end of `Checker.run` in the branch, see ADR-0019).
"""
from __future__ import annotations

from zehnlib import dialect
from zehnlib.errors import explain
from zehnlib.nodes import walk
from zehnlib.passes import static_pass
from zehnlib.stdlib import EFFECTS, SIGS
from zehnlib.types import TCon, instantiate, prune, show_t

FLAG = "effect_examples"

dialect.flag(FLAG, "off", ("off", "mock"),
             "mock: examples of effectful functions with `with <effect> = mock [..]` and `prints [..]`")

# SPEC fragment 06a, strict rule: should an effectful function satisfy "has an example" ONLY
# through a mocked example? Taken literally that makes every reference solution of the benchmark
# category `effect` fail `--strict` (their effectful functions carry pure-helper examples only),
# which contradicts the task's own "verify-refs stays OK". So the default is False: a mocked
# example *counts*, an unmocked one still counts, and E0402 stays "no example at all".
# Set True for the literal rule (E0402 when an effectful function has no mocked example).
STRICT_NEEDS_MOCKED_EXAMPLE = False

explain("E0605", "Mocked example: the `with <effect> = mock [...]` clauses do not match the effects the "
        "example needs. Every effect declared in `uses` by a function the example calls needs exactly one "
        "clause, a clause for an effect nobody in the example uses is an error, and `prints [...]` needs "
        "`with console = mock [...]`. Dialect: effect_examples=mock.")
explain("E0606", "Mocked example: the function made more calls to an effect than the mock list holds results. "
        "Add results to the list, or check why the function calls the effect so often. Effects whose "
        "functions return Unit (console) never use up results. Dialect: effect_examples=mock.")
explain("E0607", "Mocked example: a mock result does not have the type the effect's function returns "
        "(`time.now` returns Int, so `with time.now = mock [\"x\"]` is wrong), or the effect has no function "
        "whose result could be mocked. Unit has no literal, so the list of a Unit effect such as console "
        "is empty. Dialect: effect_examples=mock.")


def enabled() -> bool:
    return dialect.get(FLAG) == "mock"


def needed_effects(prog, expr) -> set:
    """Effects declared in `uses` by every user function an example expression calls or names."""
    out = set()
    for n in walk(expr):
        if n.k == "name" and n.id in prog.funcs:
            out.update(prog.funcs[n.id].uses)
    return out


def result_kind(eff):
    """How the results of effect `eff` are mocked: (kind, type).
    kind: "none" no stdlib function has the effect; "unit" every function returns Unit (nothing to list);
    "mixed" the functions disagree on the result type (no single element type); "ok" element type `type`."""
    rets = [instantiate(SIGS[n])[1] for n in sorted(EFFECTS) if EFFECTS[n] == eff]
    if not rets:
        return "none", None
    real = [r for r in rets if not _is_unit(r)]
    if not real:
        return "unit", None
    if len(real) != len(rets) or len({show_t(r) for r in real}) > 1:
        return "mixed", None
    return "ok", real[0]


def _is_unit(t) -> bool:
    t = prune(t)
    return isinstance(t, TCon) and t.name == "Unit"


def returns_unit(full: str) -> bool:
    """Does the stdlib function `full` (\"ns.fn\") return Unit?"""
    return _is_unit(instantiate(SIGS[full])[1])


def _diag(code, msg, f, cl, hint):
    return {"code": code, "severity": "error", "phase": "check", "message": msg,
            "location": {"fn": f.name, "line": cl.line, "clause": "example " + cl.text},
            "fix_hint": hint}


def example_diags(prog, strict) -> list:
    """E0605 for every mocked example whose clauses do not match what it needs; with
    STRICT_NEEDS_MOCKED_EXAMPLE also the literal strict rule. Empty unless the flag is `mock`."""
    if not enabled():
        return []
    out = []
    for f in prog.funcs.values():
        for cl in f.examples:
            mocks, prints = getattr(cl, "mocks", None) or [], getattr(cl, "prints", None)
            if not mocks and prints is None:
                continue                      # unmocked: E0602 (checker) still decides
            given = [m[0] for m in mocks]
            need = needed_effects(prog, cl.expr)
            for eff in sorted(set(e for e in given if given.count(e) > 1)):
                out.append(_diag("E0605", "effect %r has more than one mock clause" % eff, f, cl,
                                 "keep one `with %s = mock [...]` clause" % eff))
            for eff in sorted(need - set(given)):
                out.append(_diag("E0605", "the example needs effect %r but has no mock clause for it" % eff,
                                 f, cl, "add `with %s = mock [...]`" % eff))
            for eff in sorted(set(given) - need):
                out.append(_diag("E0605", "mock clause for effect %r but the example calls no function "
                                 "that declares it" % eff, f, cl, "remove the clause for %s" % eff))
            if prints is not None and "console" not in given:
                out.append(_diag("E0605", "`prints [...]` needs a `with console = mock [...]` clause", f, cl,
                                 "add `with console = mock []`"))
    if strict and STRICT_NEEDS_MOCKED_EXAMPLE:
        for f in prog.funcs.values():
            if f.uses and f.examples and not any(getattr(c, "mocks", None) for c in f.examples):
                out.append({"code": "E0402", "severity": "error", "phase": "check",
                            "message": "effectful function %r has no mocked example (strict mode)" % f.name,
                            "location": {"fn": f.name, "line": f.line},
                            "fix_hint": "add an example with `with <effect> = mock [...]`"})
    return out


@static_pass(420, "effect_examples")
def effect_examples(prog, strict, prior):
    return example_diags(prog, strict)
