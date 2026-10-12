from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fixtures", "report"))

import unittest

import report_support as S
from report_support import rec
from benchlib import metrics, stats


def rnd(i, ok, diags=(), unknown=0, tin=10, tout=5):
    return {"i": i, "tool_ok": ok, "diag_codes": list(diags), "unknown_names": unknown,
            "in_tokens": tin, "out_tokens": tout}


class DefinitionTests(unittest.TestCase):
    def setUp(self):
        self.recs = [
            # first try pass, accepted round 1
            rec(task="a", repeat=1, first=True, accepted=1, final=True, tin=100, tout=50),
            # failed first, repaired in round 2 and correct
            rec(task="a", repeat=2, first=False, accepted=2, final=True, tin=200, tout=100,
                rounds=[rnd(1, False, ["E1", "E2"], unknown=1), rnd(2, True)]),
            # accepted but wrong: silent bug
            rec(task="b", repeat=1, first=False, accepted=1, final=False, tin=100, tout=50),
            # never accepted (censored), wrong; max_rounds=3
            rec(task="b", repeat=2, first=False, accepted=None, final=False, tin=300, tout=150,
                rounds=[rnd(1, False, ["E1"], unknown=1), rnd(2, False, ["E1", "E2"]), rnd(3, False, ["E3"])]),
        ]

    def test_seven_metrics(self):
        s = metrics.summarize(self.recs, 3)
        self.assertAlmostEqual(s["pass_at_1"], 0.25)
        self.assertAlmostEqual(s["pass_repair"], 0.5)
        # repair rounds: 0, 1, 0, censored 3-1=2 -> 0.75
        self.assertAlmostEqual(s["repair_rounds"], 0.75)
        self.assertEqual(s["censored"], 1)
        self.assertAlmostEqual(s["silent_bug_rate"], 0.25)
        # unknown 2 / diagnostics (2 + 1 + 2 + 1 = 6)
        self.assertAlmostEqual(s["hallucination_rate"], 2 / 6)
        self.assertAlmostEqual(s["total_tokens"], (150 + 300 + 150 + 450) / 4)
        # variance of first_try_pass: task a [1,0] -> 0.25 ; task b [0,0] -> 0 ; mean 0.125
        self.assertAlmostEqual(s["stability"], 0.125)
        self.assertEqual(s["n_runs"], 4)
        self.assertEqual(s["n_tasks"], 2)

    def test_hallucination_without_diagnostics_is_nan(self):
        s = metrics.summarize([rec()], 3)
        self.assertNotEqual(s["hallucination_rate"], s["hallucination_rate"])

    def test_task_series_averages_repeats_then_models(self):
        recs = [rec(task="a", model="m1", repeat=1, first=True),
                rec(task="a", model="m1", repeat=2, first=True),
                rec(task="a", model="m2", repeat=1, first=False, accepted=1, final=False)]
        ser = metrics.task_series(recs, "pass_at_1", 3)
        # m1 mean 1.0, m2 mean 0.0 -> 0.5 (a pooled run mean would give 2/3)
        self.assertAlmostEqual(ser["a"], 0.5)

    def test_matches(self):
        r = rec(lang="python", variant="strict")
        self.assertTrue(metrics.matches(r, "python_strict"))
        self.assertTrue(metrics.matches(r, "python"))
        self.assertFalse(metrics.matches(r, "python_plain"))
        self.assertTrue(metrics.matches(rec(lang="zehn", variant="anything"), "zehn"))

    def test_max_rounds_from_meta_or_records(self):
        self.assertEqual(metrics.infer_max_rounds(self.recs), 3)
        self.assertEqual(metrics.infer_max_rounds(self.recs, [{"max_rounds": 5}]), 5)
        self.assertEqual(metrics.infer_max_rounds([]), 1)


class VerdictRuleTests(unittest.TestCase):
    def test_h1(self):
        self.assertEqual(metrics.verdict("H1", 0.8, 1.2), "supported")
        self.assertEqual(metrics.verdict("H1", 0.5, 0.79), "refuted")
        self.assertEqual(metrics.verdict("H1", 0.7, 0.9), "inconclusive")
        self.assertEqual(metrics.verdict("H1", 0.5, 0.8), "inconclusive")  # upper == 0.8 is not < 0.8

    def test_h2_h3(self):
        for h in ("H2", "H3"):
            self.assertEqual(metrics.verdict(h, -0.5, -0.01), "supported")
            self.assertEqual(metrics.verdict(h, 0.0, 0.5), "refuted")
            self.assertEqual(metrics.verdict(h, -0.1, 0.1), "inconclusive")
            self.assertEqual(metrics.verdict(h, -0.5, 0.0), "inconclusive")  # upper 0 is not < 0

    def test_h4(self):
        self.assertEqual(metrics.verdict("H4", -5, 0), "supported")  # upper <= 0
        self.assertEqual(metrics.verdict("H4", 0.1, 5), "refuted")
        self.assertEqual(metrics.verdict("H4", 0.0, 5), "inconclusive")  # lower 0 is not > 0
        self.assertEqual(metrics.verdict("H4", -5, 5), "inconclusive")

    def test_h5(self):
        self.assertEqual(metrics.verdict("H5", 0.01, 0.2), "supported")
        self.assertEqual(metrics.verdict("H5", -0.2, 0.0), "refuted")  # upper <= 0
        self.assertEqual(metrics.verdict("H5", 0.0, 0.2), "inconclusive")  # lower 0 is not > 0
        self.assertEqual(metrics.verdict("H5", -0.1, 0.1), "inconclusive")

    def test_nan_is_no_data(self):
        self.assertEqual(metrics.verdict("H5", float("nan"), float("nan")), "no data")

    def test_underpowered_threshold(self):
        self.assertFalse(metrics.is_underpowered(150, 5))
        self.assertTrue(metrics.is_underpowered(149, 5))
        self.assertTrue(metrics.is_underpowered(150, 4))


class FixtureVerdictTests(unittest.TestCase):
    """Each rule is hit at least once (supported, refuted, inconclusive) by a fixture."""

    @classmethod
    def setUpClass(cls):
        cls.seen = {}
        cls.by_run = {}
        for name in ("run_a", "run_good", "run_bad", "run_rounds", "run_ratio"):
            meta, recs = metrics.load_run(S.fixture(name))
            hyps = metrics.evaluate_hypotheses(recs, metrics.infer_max_rounds(recs, [meta]), n=2000)
            cls.by_run[name] = {h["id"]: h for h in hyps}
            for h in hyps:
                cls.seen.setdefault(h["id"], set()).add(h["verdict"])

    def test_every_rule_hit_all_three_ways(self):
        for hid in ("H1", "H2", "H3", "H4", "H5"):
            for v in ("supported", "refuted", "inconclusive"):
                self.assertIn(v, self.seen[hid], "%s never %s" % (hid, v))

    def test_run_a_h5_negative(self):
        h5 = self.by_run["run_a"]["H5"]
        self.assertLess(h5["est"], 0)
        self.assertEqual(h5["verdict"], "inconclusive")

    def test_missing_groups_give_no_data(self):
        self.assertEqual(self.by_run["run_ratio"]["H5"]["verdict"], "no data")
        self.assertFalse(self.by_run["run_ratio"]["H5"]["underpowered"])

    def test_fixtures_are_underpowered(self):
        for h in self.by_run["run_good"].values():
            self.assertTrue(h["underpowered"])

    def test_not_underpowered_with_150_tasks_and_5_repeats(self):
        import random
        sys_path = S.FIXTURES
        import importlib.util
        spec = importlib.util.spec_from_file_location("gen_fixtures", S.FIXTURES + "/gen_fixtures.py")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        rng = random.Random(5)
        recs = []
        for lang, variant, par in (("zehn", "default", gen.PLAIN), ("python", "plain", gen.PLAIN)):
            for task in range(150):
                for rep in range(1, 6):
                    recs.append(gen.make_record(rng, "big", task, 150, lang, variant, "m1", rep, par))
        hyps = metrics.evaluate_hypotheses(recs, 3, n=200)
        h1 = hyps[0]
        self.assertEqual(h1["n_tasks"], 150)
        self.assertEqual(h1["repeats"], 5)
        self.assertFalse(h1["underpowered"])


if __name__ == "__main__":
    unittest.main()
