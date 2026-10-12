from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fixtures", "report"))

import json
import os
import subprocess
import sys
import tempfile
import unittest

import report_support as S


def run(*args):
    return subprocess.run([sys.executable, S.REPORT_PY] + list(args), capture_output=True, text=True)


class ReportCommandTests(unittest.TestCase):
    def test_report_has_required_strings(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "r.md")
            p = run("--run", S.fixture("run_a"), "--out", out)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as fh:
                text = fh.read()
        for needle in ("H1", "H5", "GATE: H5 point estimate is worse than rust_strict",
                       "(underpowered)", "## Stability", "## Per category", "Tasks no language solved",
                       "Tasks every language solved"):
            self.assertIn(needle, text)

    def test_no_gate_when_h5_positive(self):
        p = run("--run", S.fixture("run_good"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("GATE", p.stdout)

    def test_byte_identical_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            outs = []
            for i in (1, 2):
                out = os.path.join(tmp, "r%d.md" % i)
                self.assertEqual(run("--run", S.fixture("run_a"), "--out", out).returncode, 0)
                with open(out, "rb") as fh:
                    outs.append(fh.read())
        self.assertEqual(outs[0], outs[1])
        self.assertNotIn(b"\r", outs[0])

    def test_multiple_runs_and_set_filter(self):
        p = run("--run", S.fixture("run_a"), "--run", S.fixture("run_good"), "--set", "dev")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Only records with set=dev", p.stdout)

    def test_calibration_lists_fixture_truth(self):
        p = run("--run", S.fixture("run_a"))
        # t009/t019 are impossible, t000/t010 trivial in the generated fixtures
        line_unsolved = [l for l in p.stdout.splitlines() if l.startswith("Tasks no language solved")][0]
        self.assertIn("t009", line_unsolved)
        line_all = [l for l in p.stdout.splitlines() if l.startswith("Tasks every language solved")][0]
        self.assertIn("t000", line_all)

    def test_missing_dir_is_an_error(self):
        p = run("--run", os.path.join(S.FIXTURES, "nope"))
        self.assertEqual(p.returncode, 2)
        self.assertIn("records.jsonl", p.stderr)


class AbCommandTests(unittest.TestCase):
    def test_identical_runs_keep_simpler(self):
        p = run("ab", "--a", S.fixture("run_same"), "--b", S.fixture("run_same_b"), "--simpler", "b")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("DECISION: keep b", p.stdout)
        self.assertIn("[0.000, 0.000]", p.stdout)

    def _zehn_only(self, tmp, fixture_name, out_name):
        """Copy only the zehn records of a fixture run into tmp/out_name."""
        d = os.path.join(tmp, out_name)
        os.makedirs(d)
        with open(os.path.join(S.fixture(fixture_name), "records.jsonl"), encoding="utf-8") as src, \
                open(os.path.join(d, "records.jsonl"), "w", encoding="utf-8", newline="\n") as dst:
            for line in src:
                if json.loads(line)["lang"] == "zehn":
                    dst.write(line)
        return d

    def test_a_wins_and_b_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = self._zehn_only(tmp, "run_good", "good")
            bad = self._zehn_only(tmp, "run_bad", "bad")
            p = run("ab", "--a", good, "--b", bad, "--simpler", "b")
            self.assertIn("DECISION: a wins", p.stdout)
            p = run("ab", "--a", bad, "--b", good, "--simpler", "a")
            self.assertIn("DECISION: b wins", p.stdout)

    def test_difference_within_noise_keeps_simpler(self):
        p = run("ab", "--a", S.fixture("run_a"), "--b", S.fixture("run_a"), "--simpler", "a")
        self.assertIn("DECISION: keep a", p.stdout)

    def test_ab_lists_all_seven_metrics_and_is_deterministic(self):
        args = ("ab", "--a", S.fixture("run_a"), "--b", S.fixture("run_good"), "--simpler", "a")
        p1, p2 = run(*args), run(*args)
        self.assertEqual(p1.stdout, p2.stdout)
        for label in ("pass@1", "pass_repair", "repair rounds", "silent-bug rate",
                      "hallucination rate", "total tokens", "stability"):
            self.assertIn("| " + label + " |", p1.stdout)

    def test_no_common_tasks_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "other")
            os.makedirs(d)
            with open(os.path.join(d, "records.jsonl"), "w") as fh:
                fh.write(json.dumps(S.rec(task="zzz")) + "\n")
            p = run("ab", "--a", S.fixture("run_a"), "--b", d, "--simpler", "a")
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
