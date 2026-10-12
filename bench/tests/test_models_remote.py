"""Gemini and OpenAI-compatible clients, the scheduler and run.py against a local fake HTTP server.
No network, fake keys only. Time is scaled by BENCH_TIME_SCALE so 60-second windows take about a second."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock
from urllib.parse import parse_qs, urlparse

import _common as c
from benchlib import loop, models, schema, store
from benchlib.models import ModelError
from benchlib.models.gemini import GeminiModel
from benchlib.models.openai_compat import OpenAICompatModel

KEY_A = "FAKEKEY-AAAA-1111-sentinel"
KEY_B = "FAKEKEY-BBBB-2222-sentinel"
KEYS = KEY_A + "," + KEY_B
OVERRIDES = ["--rpm", "600", "--tpm", "10000000", "--rpd", "100000"]


def fence(ext, code):
    return "```%s\n%s```\n" % (ext, code if code.endswith("\n") else code + "\n")


class FakeLLM:
    """Serves Gemini `...:generateContent` and OpenAI `.../chat/completions`. `handler(n, key, kind, body)`
    may return (status, body, headers) to override the reply; None = a correct answer."""

    def __init__(self, handler=None, delay=0.0):
        self.handler = handler
        self.delay = delay
        self.log = []
        self.lock = threading.Lock()
        self.ref_py = c.read(c.DEMO_DIR, "ref.py")
        self.ref_zehn = c.read(c.DEMO_DIR, "ref.zehn")
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                u = urlparse(self.path)
                body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))).decode("utf-8"))
                if u.path.endswith(":generateContent"):
                    kind, key = "gemini", (parse_qs(u.query).get("key") or [""])[0]
                    system = body["system_instruction"]["parts"][0]["text"]
                elif u.path.endswith("/chat/completions"):
                    kind, key = "openai", (self.headers.get("authorization") or "").replace("Bearer ", "")
                    system = body["messages"][0]["content"]
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                with outer.lock:
                    n = len(outer.log)
                    outer.log.append({"t": time.monotonic(), "key": key, "kind": kind, "body": body, "n": n})
                if outer.delay:
                    time.sleep(outer.delay)
                over = outer.handler(n, key, kind, body) if outer.handler else None
                if over is None:
                    code = outer.ref_py if system.startswith("You write a Python") else outer.ref_zehn
                    ext = "python" if system.startswith("You write a Python") else "zehn"
                    status, payload, headers = 200, outer.ok(kind, fence(ext, code)), {}
                else:
                    status, payload, headers = over
                raw = payload if isinstance(payload, str) else json.dumps(payload)
                self.send_response(status)
                self.send_header("content-type", "application/json")
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header("content-length", str(len(raw.encode("utf-8"))))
                self.end_headers()
                self.wfile.write(raw.encode("utf-8"))

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]

    @staticmethod
    def ok(kind, text, finish=None, extra_parts=()):
        if kind == "gemini":
            parts = [{"text": text}] + list(extra_parts)
            return {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": finish or "STOP"}],
                    "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 50, "thoughtsTokenCount": 20,
                                      "totalTokenCount": 170}}
        return {"choices": [{"message": {"role": "assistant", "content": text},
                             "finish_reason": "length" if finish == "MAX_TOKENS" else "stop"}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}

    @property
    def gemini_base(self):
        return "http://127.0.0.1:%d/v1beta" % self.port

    @property
    def openai_base(self):
        return "http://127.0.0.1:%d/v1" % self.port

    def __enter__(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *a):
        self.server.shutdown()
        self.server.server_close()

    def keys_seen(self):
        return {r["key"] for r in self.log}


def make_tasks(root, n):
    """n copies of the demo task, ids demo_001..: a fixture root (name starts with `_`)."""
    base = os.path.join(root, "_fix")
    for i in range(1, n + 1):
        d = os.path.join(base, "demo_%03d" % i)
        shutil.copytree(c.DEMO_DIR, d)
        meta = json.loads(c.read(d, "task.json"))
        meta["id"] = "demo_%03d" % i
        with open(os.path.join(d, "task.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f)
    return base


def run_cli(argv, env):
    import run as runmod
    out = io.StringIO()
    with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            rc = runmod.main(argv)
        except SystemExit as ex:
            rc = ex.code if isinstance(ex.code, int) else 1
            out.write(str(ex.code) if not isinstance(ex.code, int) else "")
    return rc, out.getvalue()


def records(out, run_id):
    return list(store.read_records(os.path.join(out, run_id, "records.jsonl")))


def tree_text(root):
    for base, _, files in os.walk(root):
        for fn in files:
            with open(os.path.join(base, fn), encoding="utf-8", errors="replace") as f:
                yield os.path.join(base, fn), f.read()


class Env:
    """Temp dirs + env for one CLI test."""

    def __init__(self, test, n_tasks=4, scale="60", provider="gemini", keys=KEYS):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.tmp.name, "results")
        self.tasks = make_tasks(self.tmp.name, n_tasks)
        self.scale, self.provider, self.keys = scale, provider, keys

    def env(self, llm):
        if self.provider == "gemini":
            return {"GEMINI_API_KEYS": self.keys, "GEMINI_BASE_URL": llm.gemini_base, "BENCH_TIME_SCALE": self.scale}
        return {"OPENAI_COMPAT_API_KEYS": self.keys, "OPENAI_COMPAT_BASE_URL": llm.openai_base,
                "BENCH_TIME_SCALE": self.scale}

    def argv(self, run_id, *extra, model=None, lang="python_plain", repeats="1"):
        model = model or ("gemini:fake" if self.provider == "gemini" else "openai:fake")
        return ["run", "--run-id", run_id, "--models", model, "--yes", "--lang", lang, "--repeats", repeats,
                "--tasks-dir", self.tasks, "--out", self.out] + list(extra)


class ClientRequestTests(unittest.TestCase):
    def test_gemini_request_and_response(self):
        with FakeLLM() as llm:
            m = GeminiModel("gemma-4-31b", [KEY_A], base_url=llm.gemini_base)
            thought = {"text": "```python\nBAD\n```", "thought": True}
            llm.handler = lambda n, k, kind, b: (200, FakeLLM.ok("gemini", "```python\nGOOD\n```", extra_parts=[thought]), {})
            msgs = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"},
                    {"role": "user", "content": "q2"}]
            rep = m.complete("SYS", msgs, 0.7, {})
        req = llm.log[0]
        self.assertEqual(req["key"], KEY_A)
        b = req["body"]
        self.assertEqual(b["system_instruction"], {"parts": [{"text": "SYS"}]})
        self.assertEqual([x["role"] for x in b["contents"]], ["user", "model", "user"])
        self.assertEqual(b["generationConfig"], {"temperature": 0.7, "maxOutputTokens": 8192})
        self.assertEqual(rep["text"], "```python\nGOOD\n```")          # reasoning parts are not the answer
        self.assertEqual((rep["in_tokens"], rep["out_tokens"], rep["truncated"]), (100, 70, False))  # 50 + 20 thinking

    def test_gemini_truncated_flag_and_bad_shape(self):
        self.assertTrue(GeminiModel._parse(FakeLLM.ok("gemini", "x", finish="MAX_TOKENS"))["truncated"])
        with self.assertRaises(ModelError):
            GeminiModel._parse({"candidates": []})                       # no usageMetadata
        self.assertEqual(GeminiModel._parse({"usageMetadata": {"promptTokenCount": 3}})["text"], "")

    def test_openai_request_and_response(self):
        with FakeLLM() as llm:
            m = OpenAICompatModel("llama", [KEY_A], base_url=llm.openai_base, max_output_tokens=1234)
            rep = m.complete("SYS", [{"role": "user", "content": "q"}], 0.2, {})
        req = llm.log[0]
        self.assertEqual(req["key"], KEY_A)
        self.assertEqual(req["body"]["model"], "llama")
        self.assertEqual(req["body"]["messages"][0], {"role": "system", "content": "SYS"})
        self.assertEqual((req["body"]["temperature"], req["body"]["max_tokens"]), (0.2, 1234))
        self.assertEqual((rep["in_tokens"], rep["out_tokens"], rep["truncated"]), (100, 50, False))

    def test_keys_come_from_env_and_are_deduplicated(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEYS": " %s , %s,%s," % (KEY_A, KEY_B, KEY_A)}):
            m = models.get_model("gemini:x")
        self.assertEqual(m.key_ids, ["key#1", "key#2"])
        self.assertNotIn(KEY_A, repr(m))
        env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_API_KEYS", "OPENAI_COMPAT_API_KEYS",
                                                                "OPENAI_COMPAT_BASE_URL")}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ModelError):
                models.get_model("gemini:x")
            with self.assertRaises(ModelError):
                models.get_model("openai:x")
        with mock.patch.dict(os.environ, {"OPENAI_COMPAT_API_KEYS": KEY_A}, clear=True):
            with self.assertRaises(ModelError):                          # no base url
                models.get_model("openai:x")

    def test_spec_helpers(self):
        self.assertTrue(models.is_api_model("gemini:x") and models.is_api_model("openai:x"))
        self.assertTrue(models.is_remote_model("gemini:x") and not models.is_remote_model("anthropic:x"))


class EndToEndTests(unittest.TestCase):
    def test_gemini_run_two_keys_records_tokens_and_no_key_anywhere(self):
        e = Env(self, n_tasks=6)
        with FakeLLM() as llm:
            rc, text = run_cli(e.argv("g1", *OVERRIDES, repeats="2"), e.env(llm))
            self.assertEqual(rc, 0, text)
            recs = records(e.out, "g1")
            self.assertEqual(len(recs), 12)
            self.assertEqual(len({loop.done_key(r) for r in recs}), 12)
            for r in recs:
                self.assertEqual(schema.validate_record(r), [])
                self.assertEqual((r["model"], r["accepted_round"], r["total_in_tokens"], r["total_out_tokens"]),
                                 ("gemini:fake", 1, 100, 70))
            self.assertEqual(len(llm.log), 12)
            self.assertTrue(llm.keys_seen() <= {KEY_A, KEY_B})
            meta = json.loads(c.read(e.out, "g1", "meta.json"))
            self.assertEqual(meta["models"], ["gemini:fake"])
            self.assertEqual(meta["api_hosts"], {"gemini:fake": "127.0.0.1:%d" % llm.port})
            state = json.loads(c.read(e.out, "g1", "quota_state.json"))
            self.assertEqual(sum(sum(d.values()) for d in state["days"].values()), 12)
            for path, body in list(tree_text(e.out)) + [("stdout", text)]:
                self.assertNotIn("FAKEKEY", body, path)
            self.assertIn("key#1", text)

    def test_gemini_run_with_the_shipped_limits_entry(self):
        e = Env(self, n_tasks=3, scale="400")
        with FakeLLM() as llm:
            rc, text = run_cli(["run", "--run-id", "g2", "--models", "gemini:gemma-4-31b", "--yes", "--lang",
                                "python_plain", "--repeats", "1", "--tasks-dir", e.tasks, "--out", e.out],
                               e.env(llm))
        self.assertEqual(rc, 0, text)
        self.assertEqual(len(records(e.out, "g2")), 3)
        self.assertIn("rpm=30 tpm=16000 rpd=14400", text)

    def test_openai_compatible_run(self):
        e = Env(self, n_tasks=4, provider="openai")
        with FakeLLM() as llm:
            rc, text = run_cli(e.argv("o1", *OVERRIDES), e.env(llm))
            self.assertEqual(rc, 0, text)
            recs = records(e.out, "o1")
            self.assertEqual(len(recs), 4)
            for r in recs:
                self.assertEqual((r["model"], r["total_in_tokens"], r["total_out_tokens"]), ("openai:fake", 100, 50))
            self.assertTrue(all(x["kind"] == "openai" for x in llm.log))
        for path, body in tree_text(e.out):
            self.assertNotIn("FAKEKEY", body, path)

    def test_never_more_requests_than_the_limit_in_any_window(self):
        e = Env(self, n_tasks=20, scale="60", keys=KEY_A)
        with FakeLLM() as llm:
            t0 = time.monotonic()
            rc, text = run_cli(e.argv("rate", "--rpm", "6", "--tpm", "10000000", "--rpd", "100000"), e.env(llm))
            elapsed = time.monotonic() - t0
        self.assertEqual(rc, 0, text)
        self.assertEqual(len(records(e.out, "rate")), 20)
        window = 60.0 / 60.0                      # 60 virtual seconds = 1 real second
        times = [r["t"] for r in llm.log]
        worst = max(sum(1 for u in times if t <= u < t + window) for t in times)
        self.assertLessEqual(worst, 6)            # rpm 6 (the margin 0.9 makes the target 5)
        self.assertGreater(elapsed, 2.0)          # 20 requests at 5 per window cannot finish sooner

    def test_retry_after_is_honoured(self):
        e = Env(self, n_tasks=1, scale="30", keys=KEY_A)

        def handler(n, key, kind, body):
            return (429, {"error": {"message": "slow down"}}, {"Retry-After": "30"}) if n == 0 else None

        with FakeLLM(handler) as llm:
            rc, text = run_cli(e.argv("ra", *OVERRIDES), e.env(llm))
        self.assertEqual(rc, 0, text)
        self.assertEqual(len(llm.log), 2)
        self.assertGreaterEqual(llm.log[1]["t"] - llm.log[0]["t"], 0.9)   # 30 virtual s / 30 = 1 real s
        self.assertEqual(len(records(e.out, "ra")), 1)

    def test_daily_quota_429_moves_the_work_to_the_other_key(self):
        e = Env(self, n_tasks=8)
        daily = {"error": {"code": "quota_exceeded", "message": "You exceeded your quota per day"}}

        def handler(n, key, kind, body):
            return (429, daily, {}) if key == KEY_A else None

        with FakeLLM(handler) as llm:
            rc, text = run_cli(e.argv("dq", *OVERRIDES), e.env(llm))
        self.assertEqual(rc, 0, text)
        recs = records(e.out, "dq")
        self.assertEqual(len(recs), 8)
        self.assertEqual(len({loop.done_key(r) for r in recs}), 8)
        self.assertTrue(all(r["error"] is None for r in recs))
        self.assertEqual(sum(1 for r in llm.log if r["key"] == KEY_A), 1)   # one probe, no retry loop
        self.assertIn("KEY_EXHAUSTED", text)
        self.assertNotIn("QUOTA_EXHAUSTED", text)

    def test_all_keys_exhausted_exits_zero_with_the_marker(self):
        e = Env(self, n_tasks=5)
        daily = {"error": {"code": "quota_exceeded", "message": "per day"}}
        with FakeLLM(lambda n, k, kind, b: (429, daily, {})) as llm:
            rc, text = run_cli(e.argv("qx", *OVERRIDES), e.env(llm))
        self.assertEqual(rc, 0, text)
        self.assertIn("QUOTA_EXHAUSTED remaining=5", text)
        self.assertEqual(records(e.out, "qx"), [])
        with FakeLLM() as llm2:                    # the next process starts with a probe and finishes the run
            rc, text = run_cli(e.argv("qx", "--resume", *OVERRIDES), e.env(llm2))
        self.assertEqual(rc, 0, text)
        self.assertEqual(len(records(e.out, "qx")), 5)

    def test_local_daily_budget_stops_before_the_server_says_so(self):
        e = Env(self, n_tasks=6, keys=KEY_A)
        with FakeLLM() as llm:
            rc, text = run_cli(e.argv("ld", "--rpm", "600", "--tpm", "10000000", "--rpd", "4"), e.env(llm))
        self.assertEqual(rc, 0, text)
        self.assertEqual(len(llm.log), 3)          # 4 * 0.9 -> 3 requests
        self.assertIn("QUOTA_EXHAUSTED remaining=3", text)

    def test_truncated_reply_is_recorded_and_the_model_is_told(self):
        for provider in ("gemini", "openai"):
            e = Env(self, n_tasks=1, provider=provider, keys=KEY_A)
            cut = "```python\ndef sum_above(xs, limit):\n    return sum("

            def handler(n, key, kind, body):
                return (200, FakeLLM.ok(kind, cut, finish="MAX_TOKENS"), {}) if n == 0 else None

            with FakeLLM(handler) as llm:
                rc, text = run_cli(e.argv("tr", *OVERRIDES), e.env(llm))
            self.assertEqual(rc, 0, text)
            (rec,) = records(e.out, "tr")
            self.assertEqual(rec["rounds"][0]["diag_codes"], ["TRUNCATED"])
            self.assertEqual(rec["accepted_round"], 2)
            second = json.dumps(llm.log[1]["body"])
            self.assertIn("cut off by the output limit", second)

    def test_time_budget(self):
        e = Env(self, n_tasks=10, scale="1", keys=KEY_A)
        with FakeLLM(delay=0.3) as llm:
            rc, text = run_cli(e.argv("tb", "--time-budget-minutes", "0.01", *OVERRIDES), e.env(llm))
        self.assertEqual(rc, 0, text)
        m = re.search(r"TIME_BUDGET_REACHED remaining=(\d+)", text)
        self.assertIsNotNone(m, text)
        self.assertGreater(int(m.group(1)), 0)
        self.assertEqual(len(records(e.out, "tb")) + int(m.group(1)), 10)

    def test_prefix_of_the_records_is_balanced_across_languages(self):
        e = Env(self, n_tasks=6, keys=KEY_A)
        with FakeLLM() as llm:
            rc, text = run_cli(e.argv("pb", *OVERRIDES, lang="zehn,python_plain"), e.env(llm))
        self.assertEqual(rc, 0, text)
        recs = records(e.out, "pb")
        self.assertEqual(len(recs), 12)
        counts = {"zehn": 0, "python_plain": 0}
        for r in recs:
            counts[r["lang"]] += 1
            self.assertLessEqual(abs(counts["zehn"] - counts["python_plain"]), 1)

    def test_kill_and_resume_gives_no_duplicate_and_no_missing_record(self):
        e = Env(self, n_tasks=14, keys=KEY_A)
        with FakeLLM(delay=0.25) as llm:
            env = dict(os.environ)
            env.update(e.env(llm))
            argv = [sys.executable, os.path.join(c.BENCH, "run.py")] + e.argv("kr", *OVERRIDES)
            p = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            path = os.path.join(e.out, "kr", "records.jsonl")
            deadline = time.time() + 60
            while time.time() < deadline:
                if os.path.exists(path) and len(c.read(path).splitlines()) >= 3:
                    break
                time.sleep(0.05)
            p.send_signal(signal.SIGKILL)
            p.wait()
            p.stdout.close()
            before = len(records(e.out, "kr"))
            self.assertTrue(0 < before < 14, before)
            with open(path, "a", encoding="utf-8") as f:       # a write cut short by the kill
                f.write('{"schema": 1, "run_id": "kr", "task_id": "demo_0')
            llm.delay = 0
            rc, text = run_cli(e.argv("kr", "--resume", *OVERRIDES), e.env(llm))
        self.assertEqual(rc, 0, text)
        recs = records(e.out, "kr")
        keys = [loop.done_key(r) for r in recs]
        self.assertEqual(len(keys), 14)
        self.assertEqual(len(set(keys)), 14)
        self.assertEqual({k[0] for k in keys}, {"demo_%03d" % i for i in range(1, 15)})
        self.assertIn("resume: %d of 14" % before, text)
        meta = json.loads(c.read(e.out, "kr", "meta.json"))
        self.assertEqual(len(meta["sessions"]), 2)
        state = json.loads(c.read(e.out, "kr", "quota_state.json"))
        self.assertGreaterEqual(sum(sum(d.values()) for d in state["days"].values()), len(llm.log))
        # a third resume has nothing to do and changes nothing
        with FakeLLM() as llm2:
            rc, text = run_cli(e.argv("kr", "--resume", *OVERRIDES), e.env(llm2))
        self.assertEqual((rc, len(llm2.log), len(records(e.out, "kr"))), (0, 0, 14))

    def test_server_errors_end_as_an_error_record_without_the_key(self):
        e = Env(self, n_tasks=1, scale="500", keys=KEY_A)
        with FakeLLM(lambda n, k, kind, b: (500, "internal error for key " + k, {})) as llm:
            rc, text = run_cli(e.argv("se", *OVERRIDES), e.env(llm))
        self.assertEqual(rc, 0, text)
        self.assertEqual(len(llm.log), 6)                      # six tries, then the run ends with an error
        (rec,) = records(e.out, "se")
        self.assertIn("giving up after 6 attempts", rec["error"])
        self.assertIn("key#1", rec["error"])
        for path, body in list(tree_text(e.out)) + [("stdout", text)]:
            self.assertNotIn("FAKEKEY", body, path)

    def test_bad_request_stops_the_process_without_a_record_and_without_the_key(self):
        e = Env(self, n_tasks=3, keys=KEY_A)
        with FakeLLM(lambda n, k, kind, b: (400, "bad request, key=" + k, {})) as llm:
            rc, text = run_cli(e.argv("bad", *OVERRIDES), e.env(llm))
        self.assertEqual(rc, 2, text)
        self.assertIn("FATAL", text)
        self.assertEqual(len(llm.log), 1)
        self.assertEqual(records(e.out, "bad"), [])
        for path, body in list(tree_text(e.out)) + [("stdout", text)]:
            self.assertNotIn("FAKEKEY", body, path)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.e = Env(self, n_tasks=1)
        self.env = {"GEMINI_API_KEYS": KEY_A, "GEMINI_BASE_URL": "http://127.0.0.1:9", "BENCH_TIME_SCALE": "60"}

    def test_remote_model_needs_yes(self):
        argv = [a for a in self.e.argv("x", *OVERRIDES) if a != "--yes"]
        rc, text = run_cli(argv, self.env)
        self.assertNotEqual(rc, 0)
        self.assertIn("--yes", text)
        self.assertFalse(os.path.exists(self.e.out))

    def test_model_without_limits_is_refused_before_any_call(self):
        with FakeLLM() as llm:
            rc, text = run_cli(self.e.argv("x", model="gemini:not-in-the-table"), self.e.env(llm))
            self.assertNotEqual(rc, 0)
            self.assertIn("no usable limits", text)
            self.assertEqual(llm.log, [])
            rc, text = run_cli(self.e.argv("x", model="openai:g"), dict(self.env, OPENAI_COMPAT_API_KEYS=KEY_A,
                                                                         OPENAI_COMPAT_BASE_URL=llm.openai_base))
            self.assertNotEqual(rc, 0)
            self.assertEqual(llm.log, [])

    def test_a_remote_run_uses_exactly_one_model(self):
        argv = self.e.argv("x", *OVERRIDES)
        argv[argv.index("--models") + 1] = "gemini:a"
        argv += ["--models", "gemini:b"]
        rc, text = run_cli(argv, self.env)
        self.assertNotEqual(rc, 0)
        self.assertIn("exactly one model", text)

    def test_an_existing_remote_run_is_not_overwritten_without_resume(self):
        with FakeLLM() as llm:
            self.assertEqual(run_cli(self.e.argv("x", *OVERRIDES), self.e.env(llm))[0], 0)
            rc, text = run_cli(self.e.argv("x", *OVERRIDES), self.e.env(llm))
        self.assertNotEqual(rc, 0)
        self.assertEqual(len(records(self.e.out, "x")), 1)


class StatusAndDoctorTests(unittest.TestCase):
    def test_status_counts_done_and_remaining(self):
        e = Env(self, n_tasks=6, keys=KEY_A)
        with FakeLLM() as llm:
            run_cli(e.argv("st", "--time-budget-minutes", "0.0001", *OVERRIDES, lang="zehn,python_plain"), e.env(llm))
            n = len(records(e.out, "st"))
            rc, text = run_cli(["status", "--run-id", "st", "--out", e.out, "--lang", "zehn,python_plain",
                                "--tasks-dir", e.tasks, "--repeats", "1"], {})
        self.assertEqual(rc, 0, text)
        self.assertIn("done: %d" % n, text)
        self.assertIn("remaining: %d" % (12 - n), text)
        self.assertIn("models: gemini:fake", text)
        self.assertIn("estimated remaining calls", text)

    def test_status_of_a_run_that_does_not_exist_yet(self):
        e = Env(self, n_tasks=3)
        rc, text = run_cli(["status", "--run-id", "new", "--out", e.out, "--lang", "python_plain", "--tasks-dir",
                            e.tasks, "--repeats", "2", "--models", "gemini:fake"], {})
        self.assertEqual(rc, 0, text)
        self.assertIn("done: 0", text)
        self.assertIn("remaining: 6", text)
        self.assertIn("assumed", text)

    def test_doctor_ok(self):
        rc, text = run_cli(["doctor", "--lang", "zehn,python_plain"], {})
        self.assertEqual(rc, 0, text)
        self.assertIn("python ", text)
        self.assertIn("OK      zehn", text)
        self.assertIn("OK      python_plain", text)

    def test_doctor_reports_a_missing_tool_with_a_nonzero_exit(self):
        p = subprocess.run([sys.executable, os.path.join(c.BENCH, "run.py"), "doctor", "--lang", "zehn,ts_strict"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                           env={"PATH": os.path.join(tempfile.gettempdir(), "no-such-dir-for-doctor")})
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn("MISSING ts_strict", p.stdout)
        self.assertIn("OK      zehn", p.stdout)


class WorkflowTests(unittest.TestCase):
    """Structure checks of .github/workflows/baseline.yml with the standard library only (the workflow was
    not executed anywhere). If PyYAML happens to be installed it is also used as a second parser."""

    PATH = os.path.join(c.ROOT, ".github", "workflows", "baseline.yml")

    def setUp(self):
        with open(self.PATH, encoding="utf-8", newline="") as f:
            self.text = f.read()

    def test_plain_text_shape(self):
        self.assertNotIn("\t", self.text)
        self.assertNotIn("\r", self.text)
        self.assertTrue(self.text.endswith("\n"))
        self.assertEqual(self.text.count("${{"), self.text.count("}}"))
        for line in self.text.splitlines():
            self.assertEqual((len(line) - len(line.lstrip(" "))) % 2, 0, line)

    def test_top_level_keys_and_jobs(self):
        top = re.findall(r"^([a-z_]+):", self.text, re.MULTILINE)
        self.assertEqual(top, ["name", "on", "concurrency", "permissions", "jobs"])
        jobs = re.findall(r"^  ([a-z_]+):\s*$", self.text.split("\njobs:\n")[1], re.MULTILINE)
        self.assertEqual(jobs, ["plan", "run", "persist"])
        for must in ("workflow_dispatch:", "schedule:", 'cron: "0 */6 * * *"', "group: baseline",
                     "cancel-in-progress: false", "fail-fast: false", "timeout-minutes: 355",
                     'python-version: "3.12"', "python3 -m pip install mypy ruff", "npm install -g typescript",
                     "rustup component add clippy rustfmt", "bench-data", "bench/run.py doctor",
                     "bench/run.py status", "--resume --yes --time-budget-minutes 330", "if: always()",
                     "contents: write", "bench/report.py", "REPORT.md", "name: baseline-results",
                     "name: results-${{ matrix.model.slug }}", "git pull --rebase", "BASELINE_MODELS",
                     "fromJSON(needs.plan.outputs.models)", "needs: [plan, run]"):
            self.assertIn(must, self.text)
        for name in ("models", "repeats", "langs", "only", "run_id"):
            self.assertRegex(self.text, r"(?m)^      %s:\n        description:" % name)
        self.assertIn("steps.status.outputs.remaining != '0'", self.text)

    def test_every_job_has_runs_on_and_steps(self):
        body = self.text.split("\njobs:\n")[1]
        blocks = re.split(r"(?m)^  (?=[a-z_]+:\s*$)", body)[1:]
        self.assertEqual(len(blocks), 3)
        for b in blocks:
            self.assertRegex(b, r"(?m)^    runs-on: ubuntu-latest$")
            self.assertRegex(b, r"(?m)^    steps:$")

    def test_only_the_allowed_secrets_and_variables_and_no_environment_echo(self):
        self.assertEqual(set(re.findall(r"secrets\.([A-Za-z_]+)", self.text)),
                         {"GEMINI_API_KEYS", "OPENAI_COMPAT_API_KEYS"})
        self.assertEqual(set(re.findall(r"vars\.([A-Za-z_]+)", self.text)),
                         {"BASELINE_MODELS", "OPENAI_COMPAT_BASE_URL"})
        for bad in ("printenv", "set -x", "env |", "env>", "toJSON(secrets", "toJSON(env", "toJSON(github",
                    "ACTIONS_STEP_DEBUG", "echo ${{ secrets"):
            self.assertNotIn(bad, self.text)
        # secrets are given to the run step only, never at job or workflow level
        for m in re.finditer(r"secrets\.", self.text):
            before = self.text[:m.start()].splitlines()
            self.assertTrue(any(l.strip() == "- name: run" for l in before[-6:]), before[-6:])

    def test_pyyaml_agrees_when_available(self):
        try:
            import yaml
        except ImportError:
            return
        doc = yaml.safe_load(self.text)
        self.assertEqual(sorted(doc["jobs"]), ["persist", "plan", "run"])
        self.assertEqual(doc["jobs"]["run"]["strategy"]["fail-fast"], False)
        self.assertEqual(doc["jobs"]["run"]["timeout-minutes"], 355)
        self.assertEqual(doc["jobs"]["persist"]["permissions"], {"contents": "write"})
        self.assertEqual(doc[True]["schedule"], [{"cron": "0 */6 * * *"}])
        self.assertEqual(sorted(doc[True]["workflow_dispatch"]["inputs"]),
                         ["langs", "models", "only", "repeats", "run_id"])


if __name__ == "__main__":
    unittest.main()
