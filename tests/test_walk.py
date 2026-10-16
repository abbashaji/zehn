"""TASK 05: zehnlib.nodes.walk, the generic AST walker."""
from __future__ import annotations

import os
import unittest

from test_registry import ROOT

import zehn
from zehnlib import nodes
from zehnlib.nodes import N, walk

# kinds named in the task, plus the two statement kinds the parser builds from `let` / `var`,
# plus the two kinds TASK_07 added (tuple expression, tuple pattern)
SPEC_KINDS = {"assign", "bin", "bool", "call", "clause", "ctor", "expr", "field", "fn", "if", "int",
              "list", "match", "name", "neg", "not", "pbind", "plit", "pvariant", "pwild", "record",
              "return", "str", "try", "let", "var", "tuple", "ptuple"}


# The kinds that examples/ never uses (var, assignment, not, bool, bare expression, literal and
# wildcard patterns), so that together with examples/ every kind the parser builds is walked.
COVERAGE_SRC = """fn g(n: Int, b: Bool) -> Int
  example g(0, true) == 0
do
  var acc = 0
  let t = not b
  acc := acc + 1
  list.len([1])
  match n do
    case 0 =>
      return 0
    case _ =>
      return acc
  end match
end fn

fn h(b: Bool) -> Int
  example h(true) == 1
do
  match b do
    case true =>
      return 1
    case false =>
      return 2
  end match
end fn
"""


def example_sources():
    """Every program in examples/, plus COVERAGE_SRC."""
    out = [("<coverage>", COVERAGE_SRC)]
    folder = os.path.join(ROOT, "examples")
    for fname in sorted(os.listdir(folder)):
        if fname.endswith(".zehn"):
            with open(os.path.join(folder, fname), encoding="utf-8") as fh:
                out.append((fname, fh.read()))
    return out


def parse_recording(src):
    """Parse `src`; also return every N the parser created, in creation order."""
    created, orig = [], N.__init__

    def spy(self, *a, **kw):
        orig(self, *a, **kw)
        created.append(self)

    N.__init__ = spy
    try:
        prog = zehn.parse(src)
    finally:
        N.__init__ = orig
    return prog, created


def reference_preorder(n, seen=None):
    """A deliberately plain recursive version of the same specification."""
    seen = set() if seen is None else seen
    if id(n) in seen:
        return []
    seen.add(id(n))
    out = [n]

    def kids(v):
        if isinstance(v, N):
            out.extend(reference_preorder(v, seen))
        elif isinstance(v, (list, tuple)):
            for x in v:
                kids(x)
        elif isinstance(v, dict):
            for x in v.values():
                kids(x)

    for v in n.__dict__.values():
        kids(v)
    return out


class WalkOnExamples(unittest.TestCase):
    def test_walk_reaches_exactly_the_nodes_the_parser_built_once_each(self):
        seen_kinds = set()
        for fname, src in example_sources():
            with self.subTest(program=fname):
                prog, created = parse_recording(src)
                visited = []
                for fn in prog.funcs.values():
                    visited += list(walk(fn))
                ids = [id(n) for n in visited]
                self.assertEqual(len(ids), len(set(ids)), "a node was visited twice")
                self.assertEqual(set(ids), {id(n) for n in created})
                seen_kinds |= {n.k for n in visited}
        self.assertEqual(seen_kinds, SPEC_KINDS)

    def test_every_node_kind_the_parser_can_build_is_walked(self):
        import re
        with open(os.path.join(ROOT, "zehnlib", "parser.py"), encoding="utf-8") as fh:
            text = fh.read()
        built = set(re.findall(r'\bN\("([a-z_]+)"', text)) | {"let", "var"}   # let/var: N(c[1], ...)
        seen = set()
        for _, src in example_sources():
            for fn in zehn.parse(src).funcs.values():
                seen |= {n.k for n in walk(fn)}
        self.assertEqual(built - seen, set(), "kinds missing from examples/ + COVERAGE_SRC")
        self.assertEqual(seen - built, set())
        self.assertTrue(SPEC_KINDS <= seen)

    def test_order_is_pre_order_and_matches_a_plain_recursive_reference(self):
        for fname, src in example_sources():
            with self.subTest(program=fname):
                for fn in zehn.parse(src).funcs.values():
                    got = list(walk(fn))
                    self.assertIs(got[0], fn)
                    self.assertEqual([id(n) for n in got], [id(n) for n in reference_preorder(fn)])

    def test_parent_comes_before_its_children(self):
        src = "fn f(x: Int) -> Int\n  example f(1) == 2\ndo\n  return x + 1\nend fn\n"
        fn = zehn.parse(src).funcs["f"]
        order = list(walk(fn))
        self.assertEqual(order[0].k, "fn")
        ret = fn.body[0]
        self.assertLess(order.index(ret), order.index(ret.expr))     # the `x + 1` after its `return`
        self.assertLess(order.index(ret.expr), order.index(ret.expr.l))


class WalkOnHandBuiltTrees(unittest.TestCase):
    def test_shared_node_is_visited_once(self):
        shared = N("int", 1, v=1)
        root = N("bin", 1, op="+", l=shared, r=shared)
        self.assertEqual([n.k for n in walk(root)], ["bin", "int"])

    def test_cycle_terminates(self):
        a, b = N("a", 1), N("b", 1)
        a.child, b.child = b, a
        self.assertEqual([n.k for n in walk(a)], ["a", "b"])

    def test_containers_lists_tuples_dict_values_and_nesting(self):
        leaves = [N("leaf%d" % i, 1) for i in range(6)]
        root = N("root", 1, xs=[leaves[0], (leaves[1], [leaves[2]])], d={"k": leaves[3], "j": [leaves[4]]},
                 one=leaves[5])
        self.assertEqual([n.k for n in walk(root)],
                         ["root", "leaf0", "leaf1", "leaf2", "leaf3", "leaf4", "leaf5"])

    def test_non_node_values_are_ignored(self):
        root = N("root", 3, name="x", n=5, flag=True, nothing=None, text=["a", ("b", 1)], v=object())
        self.assertEqual([n.k for n in walk(root)], ["root"])

    def test_a_new_node_kind_needs_no_walker_change(self):
        root = N("brand_new_kind", 1, payload=[N("another_new_kind", 2, inner=N("int", 2, v=0))])
        self.assertEqual([n.k for n in walk(root)], ["brand_new_kind", "another_new_kind", "int"])

    def test_deeply_nested_tree_does_not_exhaust_the_host_stack(self):
        root = cur = N("neg", 1)
        for _ in range(50000):
            nxt = N("neg", 1)
            cur.expr = nxt
            cur = nxt
        self.assertEqual(sum(1 for _ in walk(root)), 50001)

    def test_walk_is_lazy_and_exported(self):
        self.assertTrue(hasattr(walk(N("x", 1)), "__next__"))
        self.assertIs(nodes.walk, walk)


if __name__ == "__main__":
    unittest.main()
