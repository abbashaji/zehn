from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fixtures", "report"))

import unittest

import report_support as S
from benchlib import metrics, stats


class BootstrapTests(unittest.TestCase):
    def test_constant_data_is_degenerate(self):
        lo, hi = stats.bootstrap_ci([0.1, 0.1, 0.1, 0.1, 0.1], n=200)
        self.assertEqual(lo, hi)
        self.assertAlmostEqual(lo, 0.1)

    def test_empty_gives_nan(self):
        lo, hi = stats.bootstrap_ci([])
        self.assertNotEqual(lo, lo)
        self.assertNotEqual(hi, hi)

    def test_interval_brackets_the_mean(self):
        vals = [0, 1, 1, 0, 1, 1, 1, 0, 1, 1]
        lo, hi = stats.bootstrap_ci(vals, n=2000)
        self.assertLessEqual(lo, stats.mean(vals))
        self.assertGreaterEqual(hi, stats.mean(vals))
        self.assertLess(lo, hi)

    def test_same_seed_same_output(self):
        vals = [0.2, 0.9, 0.4, 0.5, 0.7, 0.1]
        self.assertEqual(stats.bootstrap_ci(vals, n=500, seed=7), stats.bootstrap_ci(vals, n=500, seed=7))
        self.assertNotEqual(stats.bootstrap_ci(vals, n=500, seed=7), stats.bootstrap_ci(vals, n=500, seed=8))

    def test_custom_stat(self):
        vals = [1.0, 2.0, 3.0, 100.0]
        lo, hi = stats.bootstrap_ci(vals, stat=max, n=200)
        self.assertEqual(hi, 100.0)

    def test_defaults_match_spec(self):
        import inspect
        sig = inspect.signature(stats.bootstrap_ci)
        self.assertIs(sig.parameters["stat"].default, stats.mean)
        self.assertEqual(sig.parameters["n"].default, 10000)
        self.assertEqual(sig.parameters["seed"].default, 1234)
        self.assertEqual(sig.parameters["alpha"].default, 0.05)

    def test_variance_is_population(self):
        self.assertAlmostEqual(stats.variance([0, 1]), 0.25)
        self.assertEqual(stats.variance([1, 1, 1]), 0.0)


class PairedTests(unittest.TestCase):
    def test_identical_data_gives_zero_interval(self):
        vals = [0.1, 0.7, 0.3, 0.9, 0.5]
        self.assertEqual(stats.paired_diff_ci(vals, list(vals), n=300), (0.0, 0.0, 0.0))

    def test_resamples_tasks_pairwise(self):
        # a is b + 1 for every task, so the difference is 1 in every resample.
        b = [0.0, 0.5, 0.2, 0.9, 0.4]
        a = [x + 1 for x in b]
        est, lo, hi = stats.paired_diff_ci(a, b, n=300)
        self.assertAlmostEqual(est, 1.0)
        self.assertAlmostEqual(lo, 1.0)
        self.assertAlmostEqual(hi, 1.0)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            stats.paired_diff_ci([1, 2], [1])

    def test_ratio_ci_contains_true_ratio_of_fixture(self):
        _meta, recs = metrics.load_run(S.fixture("run_ratio"))
        zehn = [r for r in recs if metrics.matches(r, "zehn")]
        plain = [r for r in recs if metrics.matches(r, "python_plain")]
        res = metrics.paired(zehn, plain, "pass_at_1", 2, "ratio")
        self.assertAlmostEqual(res["est"], 0.8)
        self.assertLessEqual(res["lo"], 0.8)
        self.assertGreaterEqual(res["hi"], 0.8)

    def test_ratio_drops_zero_denominator_resamples(self):
        est, lo, hi = stats.paired_ratio_ci([1.0, 1.0], [0.0, 1.0], n=200)
        self.assertEqual(lo, lo)  # finite


if __name__ == "__main__":
    unittest.main()
