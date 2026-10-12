"""Scheduler, limiter, day counter, worker pool, work order and resume repair: no network, no real sleeping."""
from __future__ import annotations

import json
import os
import random
import tempfile
import unittest

import _common as c  # noqa: F401  (puts bench/ on sys.path)
from benchlib import loop, store
from benchlib.models import FatalModelError, HttpError, KeyExhausted, ModelError, NetworkError
from benchlib.models import scheduler as S


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps = []
        self.date = "2026-10-12"

    def now(self):
        return self.t

    def sleep(self, s):
        if s > 0:
            self.sleeps.append(s)
            self.t += s

    def utc_date(self):
        return self.date


def limiter(clock, rpm=6, tpm=100000, rpd=1000, margin=0.9, quota=None, key="key#1"):
    return S.KeyLimiter(key, rpm, tpm, rpd, margin, clock, quota or S.QuotaState(None, clock))


class LimiterTests(unittest.TestCase):
    def test_rpm_sliding_window(self):
        clock = FakeClock()
        lim = limiter(clock)                     # 6 * 0.9 -> 5 per 60 s
        stamps = []
        for _ in range(11):
            lim.acquire(10)
            stamps.append(clock.t)
        for i, t in enumerate(stamps):           # never more than 5 starts inside any 60 s window
            self.assertLessEqual(sum(1 for u in stamps if t <= u < t + 60.0), 5)
        self.assertGreaterEqual(stamps[5] - stamps[0], 60.0)
        self.assertGreaterEqual(stamps[10] - stamps[0], 120.0)

    def test_tpm_waits_for_tokens_to_leave_the_window(self):
        clock = FakeClock()
        lim = limiter(clock, rpm=100, tpm=1000)  # 900 tokens per minute
        t0 = clock.t
        lim.acquire(500)
        lim.acquire(300)
        self.assertEqual(clock.t, t0)            # 800 <= 900: no wait
        lim.acquire(300)                         # 1100 > 900: must wait for the first 500 to expire
        self.assertGreaterEqual(clock.t - t0, 60.0)
        self.assertLess(clock.t - t0, 61.0)

    def test_settle_corrects_the_estimate(self):
        clock = FakeClock()
        lim = limiter(clock, rpm=100, tpm=1000)
        e = lim.acquire(800)
        lim.settle(e, 100)                       # the real usage was small: the room is given back
        t0 = clock.t
        lim.acquire(800)
        self.assertEqual(clock.t, t0)

    def test_oversized_request_goes_through_an_empty_window(self):
        clock = FakeClock()
        lim = limiter(clock, rpm=100, tpm=1000)
        t0 = clock.t
        lim.acquire(5000)                        # cannot ever fit: it is sent alone, not deadlocked
        self.assertEqual(clock.t, t0)

    def test_daily_budget_exhausts_the_key_and_new_date_resets(self):
        clock = FakeClock()
        quota = S.QuotaState(None, clock)
        lim = limiter(clock, rpm=1000, rpd=10, quota=quota)   # 9 per day
        for _ in range(9):
            lim.acquire(1)
        with self.assertRaises(KeyExhausted):
            lim.acquire(1)
        clock.date = "2026-10-13"
        lim.acquire(1)                                         # the counter is per UTC date

    def test_quota_state_persists_and_holds_no_key(self):
        clock = FakeClock()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "run", "quota_state.json")
            q = S.QuotaState(path, clock)
            q.add("key#1")
            q.add("key#1")
            q.add("key#2")
            q2 = S.QuotaState(path, clock)
            self.assertEqual((q2.count("key#1"), q2.count("key#2"), q2.count("key#3")), (2, 1, 0))
            data = json.loads(c.read(path))
            self.assertEqual(data["days"]["2026-10-12"], {"key#1": 2, "key#2": 1})
            with open(path, "w") as f:
                f.write("{not json")
            self.assertEqual(S.QuotaState(path, clock).count("key#1"), 0)


class ScriptedModel:
    name = "gemini:scripted"
    key_ids = ["key#1"]

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def complete_with_key(self, idx, system, messages, temperature, ctx):
        self.calls += 1
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


OK = {"text": "x", "in_tokens": 10, "out_tokens": 5}
MSG = [{"role": "user", "content": "hi"}]


def key_client(model, clock, **kw):
    lim = limiter(clock, rpm=1000, rpd=1000)
    return S.KeyClient(model, 0, lim, 1500, clock, random.Random(1), lambda t: None), lim


class KeyClientTests(unittest.TestCase):
    def test_retry_after_is_honoured(self):
        clock = FakeClock()
        m = ScriptedModel([HttpError(429, "slow down", 17.0), OK])
        kc, _ = key_client(m, clock)
        self.assertEqual(kc.complete("s", MSG, 1.0, {}), OK)
        self.assertEqual(m.calls, 2)
        self.assertIn(17.0, clock.sleeps)

    def test_backoff_without_retry_after_grows_and_stops_after_six_tries(self):
        clock = FakeClock()
        m = ScriptedModel([HttpError(503, "busy")] * 6)
        kc, _ = key_client(m, clock)
        with self.assertRaises(ModelError) as cm:
            kc.complete("s", MSG, 1.0, {})
        self.assertIn("giving up after 6 attempts", str(cm.exception))
        self.assertEqual(m.calls, 6)
        waits = [s for s in clock.sleeps]
        self.assertEqual(len(waits), 5)
        for n, w in enumerate(waits, 1):          # 2 * 2^(n-1) with jitter in [0.5, 1.0]
            top = min(60.0, 2.0 * 2 ** (n - 1))
            self.assertTrue(0.5 * top <= w <= top, (n, w))

    def test_network_error_is_retried(self):
        clock = FakeClock()
        m = ScriptedModel([NetworkError("timeout"), OK])
        kc, _ = key_client(m, clock)
        self.assertEqual(kc.complete("s", MSG, 1.0, {}), OK)

    def test_daily_quota_429_exhausts_the_key_without_retry(self):
        clock = FakeClock()
        m = ScriptedModel([HttpError(429, '{"error": {"code": "quota_exceeded", "message": "per day"}}')])
        kc, _ = key_client(m, clock)
        with self.assertRaises(KeyExhausted):
            kc.complete("s", MSG, 1.0, {})
        self.assertTrue(kc.exhausted)
        self.assertEqual(m.calls, 1)

    def test_non_transient_status_is_fatal(self):
        for status in (400, 401, 403, 404):
            m = ScriptedModel([HttpError(status, "no")])
            kc, _ = key_client(m, FakeClock())
            with self.assertRaises(FatalModelError):
                kc.complete("s", MSG, 1.0, {})

    def test_retries_count_against_the_day_counter(self):
        clock = FakeClock()
        m = ScriptedModel([HttpError(503, "busy"), OK])
        kc, lim = key_client(m, clock)
        kc.complete("s", MSG, 1.0, {})
        self.assertEqual(lim.quota.count("key#1"), 2)

    def test_token_estimate(self):
        self.assertEqual(S.estimate_tokens("a" * 350, [{"role": "user", "content": "b" * 350}], 1500), 200 + 1500)


class LimitsTests(unittest.TestCase):
    TABLE = {"gemini:m": {"rpm": 5, "tpm": 100, "rpd": 7}, "openai:g": {"rpm": None, "tpm": None, "rpd": None}}

    def test_resolve(self):
        self.assertEqual(S.resolve_limits("gemini:m", self.TABLE, {}), {"rpm": 5, "tpm": 100, "rpd": 7})
        self.assertEqual(S.resolve_limits("gemini:m", self.TABLE, {"rpm": 1})["rpm"], 1)
        self.assertEqual(S.resolve_limits("gemini:new", {}, {"rpm": 1, "tpm": 2, "rpd": 3}),
                         {"rpm": 1, "tpm": 2, "rpd": 3})

    def test_missing_or_null_is_refused(self):
        for spec, over in (("gemini:unknown", {}), ("openai:g", {}), ("gemini:unknown", {"rpm": 3})):
            with self.assertRaises(ModelError):
                S.resolve_limits(spec, self.TABLE, over)

    def test_shipped_table(self):
        table = S.load_limits(os.path.join(c.BENCH, "limits.json"))
        want = {"gemini:gemma-4-31b": (30, 16000, 14400), "gemini:gemma-4-26b": (30, 16000, 14400),
                "gemini:gemini-3.1-flash-lite": (15, 250000, 500), "gemini:gemini-3.5-flash-lite": (15, 250000, 500),
                "gemini:gemini-2.5-flash-lite": (10, 250000, 20), "gemini:gemini-2.5-flash": (5, 250000, 20)}
        for spec, (rpm, tpm, rpd) in want.items():
            self.assertEqual(S.resolve_limits(spec, table, {}), {"rpm": rpm, "tpm": tpm, "rpd": rpd})
        raw = json.loads(c.read(c.BENCH, "limits.json"))
        self.assertIn("_note", raw)
        nulls = [k for k, v in raw.items() if not k.startswith("_") and v["rpm"] is None]
        self.assertTrue(nulls)                    # Groq placeholders are null, never invented numbers
        for k in nulls:
            self.assertEqual(raw[k], {"rpm": None, "tpm": None, "rpd": None})


class PoolTests(unittest.TestCase):
    class W:
        def __init__(self, name, dies=False):
            self.name, self.dies = name, dies

    def test_exhausted_key_requeues_its_run_and_the_other_key_finishes(self):
        a, b = self.W("a", dies=True), self.W("b")
        seen = []

        def execute(item, w):
            if w.dies:
                raise KeyExhausted("a is out")
            seen.append(item)
            return item

        got = []
        res = S.run_pool(list(range(6)), [a, b], execute, got.append, FakeClock(), None, lambda t: None)
        self.assertEqual(sorted(got), list(range(6)))
        self.assertEqual(sorted(seen), list(range(6)))
        self.assertEqual((res.done, res.remaining, res.fatal), (6, [], None))

    def test_all_keys_exhausted_leaves_the_queue(self):
        def execute(item, w):
            raise KeyExhausted("out")

        res = S.run_pool(list(range(5)), [self.W("a"), self.W("b")], execute, lambda r: None,
                         FakeClock(), None, lambda t: None)
        self.assertEqual(sorted(res.remaining), list(range(5)))
        self.assertFalse(res.budget_reached)

    def test_fatal_stops_everything_and_keeps_the_item(self):
        def execute(item, w):
            raise FatalModelError("bad key")

        res = S.run_pool([1, 2, 3], [self.W("a")], execute, lambda r: None, FakeClock(), None, lambda t: None)
        self.assertEqual(res.fatal, "bad key")
        self.assertEqual(sorted(res.remaining), [1, 2, 3])

    def test_time_budget_stops_new_runs_only(self):
        clock = FakeClock()
        done = []

        def execute(item, w):
            clock.t += 10.0                       # every run takes 10 s
            return item

        res = S.run_pool(list(range(10)), [self.W("a")], execute, done.append, clock, 0.5, lambda t: None)
        self.assertTrue(res.budget_reached)
        self.assertEqual(done, [0, 1, 2])         # 30 s budget: three runs started, the third one finished
        self.assertEqual(res.remaining, list(range(3, 10)))


def tasks(n, cats=("pure", "text", "domain")):
    return [{"id": "%s_%03d" % (cats[i % len(cats)], i), "category": cats[i % len(cats)]} for i in range(n)]


class Ad:
    def __init__(self, name):
        self.name = name


class OrderTests(unittest.TestCase):
    def test_language_counts_differ_by_at_most_one_in_every_prefix(self):
        for n_tasks in (1, 5, 30):
            for n_langs in range(1, 7):
                langs = [Ad("l%d" % i) for i in range(n_langs)]
                order = list(loop.work_order(tasks(n_tasks), langs, ["m"], 3, 1234))
                self.assertEqual(len(order), n_tasks * n_langs * 3)
                counts = {l.name: 0 for l in langs}
                for n, (t, ad, spec, rep) in enumerate(order, 1):
                    counts[ad.name] += 1
                    self.assertLessEqual(max(counts.values()) - min(counts.values()), 1, (n_tasks, n_langs, n))

    def test_repeat_major_and_each_pair_once(self):
        order = list(loop.work_order(tasks(12), [Ad("a"), Ad("b")], ["m"], 3, 7))
        self.assertEqual([o[3] for o in order], sorted(o[3] for o in order))
        self.assertEqual(len({(o[0]["id"], o[1].name, o[3]) for o in order}), 12 * 2 * 3)

    def test_categories_are_interleaved(self):
        order = list(loop.work_order(tasks(30), [Ad("a")], ["m"], 1, 5))   # 10 tasks per category
        counts = {}
        for n, (t, _, _, _) in enumerate(order, 1):
            counts[t["category"]] = counts.get(t["category"], 0) + 1
            self.assertLessEqual(max(counts.values()) - min(list(counts.values()) + [0] * (3 - len(counts))), 1)

    def test_seed_and_repeat_independence(self):
        a = [(t["id"], l.name) for t, l, _, r in loop.work_order(tasks(12), [Ad("a"), Ad("b")], ["m"], 1, 99)]
        b = [(t["id"], l.name) for t, l, _, r in loop.work_order(tasks(12), [Ad("a"), Ad("b")], ["m"], 4, 99) if r == 1]
        d = [(t["id"], l.name) for t, l, _, r in loop.work_order(tasks(12), [Ad("a"), Ad("b")], ["m"], 1, 100)]
        self.assertEqual(a, b)                    # repeat 1 does not depend on how many repeats are asked
        self.assertNotEqual(a, d)


class RepairTests(unittest.TestCase):
    def test_partial_last_line_is_dropped_and_complete_lines_kept(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "records.jsonl")
            with open(p, "w") as f:
                f.write('{"a": 1}\n{"a": 2}\n{"a": ')
            store.repair_records(p)
            self.assertEqual(c.read(p), '{"a": 1}\n{"a": 2}\n')

    def test_complete_last_line_without_newline_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "records.jsonl")
            with open(p, "w") as f:
                f.write('{"a": 1}\n{"a": 2}')
            store.repair_records(p)
            self.assertEqual(c.read(p), '{"a": 1}\n{"a": 2}\n')

    def test_broken_middle_line_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "records.jsonl")
            with open(p, "w") as f:
                f.write('{"a": 1}\nnope\n{"a": 2}\n')
            with self.assertRaises(ValueError):
                store.repair_records(p)


if __name__ == "__main__":
    unittest.main()
