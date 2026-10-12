from __future__ import annotations

import contextlib
import http.server
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

import _common as c
from benchlib import schema, store
from benchlib.models import ModelError, get_model, is_api_model
from benchlib.models.anthropic import AnthropicModel

SENTINEL = "sk-test-SENTINEL-do-not-leak-123"


class FakeAPI:
    """Local stand-in for the Messages API. `script` is a list of (status, body) answered in order."""

    def __init__(self, script):
        self.script, self.requests = list(script), []
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("content-length", "0"))
                outer.requests.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()},
                                       "body": json.loads(self.rfile.read(n))})
                i = min(len(outer.requests) - 1, len(outer.script) - 1)
                status, body = outer.script[i]
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        self.server = http.server.HTTPServer(("127.0.0.1", 0), H)
        self.url = "http://127.0.0.1:%d/v1/messages" % self.server.server_port
        self.base = "http://127.0.0.1:%d" % self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *a):
        self.server.shutdown()
        self.server.server_close()


def ok_body(text, i=11, o=7):
    return {"content": [{"type": "text", "text": text}], "usage": {"input_tokens": i, "output_tokens": o}}


class AnthropicClientTests(unittest.TestCase):
    def test_request_shape_and_usage(self):
        with FakeAPI([(200, ok_body("hello", 12, 3))]) as api:
            m = AnthropicModel("some-model", url=api.url, api_key=SENTINEL, sleep=lambda s: None)
            r = m.complete("SYS", [{"role": "user", "content": "hi"}], 0.5, {})
        self.assertEqual(r, {"text": "hello", "in_tokens": 12, "out_tokens": 3})
        req = api.requests[0]
        self.assertEqual(req["path"], "/v1/messages")
        self.assertEqual(req["headers"]["x-api-key"], SENTINEL)
        self.assertIn("anthropic-version", req["headers"])
        self.assertEqual(req["body"], {"model": "some-model", "max_tokens": 4096, "temperature": 0.5,
                                       "system": "SYS", "messages": [{"role": "user", "content": "hi"}]})
        self.assertNotIn(SENTINEL, repr(m))

    def test_retries_429_and_5xx_with_backoff(self):
        sleeps = []
        script = [(429, {"error": "slow"}), (503, {"error": "down"}), (200, ok_body("done"))]
        with FakeAPI(script) as api:
            m = AnthropicModel("m", url=api.url, api_key=SENTINEL, sleep=sleeps.append)
            self.assertEqual(m.complete("s", [{"role": "user", "content": "x"}], 1.0, {})["text"], "done")
        self.assertEqual(len(api.requests), 3)
        self.assertEqual(sleeps, [1.0, 2.0])

    def test_gives_up_and_does_not_retry_4xx(self):
        with FakeAPI([(500, {"error": "x"})]) as api:
            m = AnthropicModel("m", url=api.url, api_key=SENTINEL, sleep=lambda s: None, max_attempts=3)
            with self.assertRaises(ModelError):
                m.complete("s", [], 1.0, {})
            self.assertEqual(len(api.requests), 3)
        with FakeAPI([(400, {"error": "bad request"})]) as api:
            m = AnthropicModel("m", url=api.url, api_key=SENTINEL, sleep=lambda s: None)
            with self.assertRaises(ModelError):
                m.complete("s", [], 1.0, {})
            self.assertEqual(len(api.requests), 1)

    def test_missing_key(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with self.assertRaises(ModelError):
                AnthropicModel("m")

    def test_get_model(self):
        self.assertTrue(is_api_model("anthropic:x"))
        self.assertFalse(is_api_model("stub:perfect"))
        with self.assertRaises(ModelError):
            get_model("stub:nope")
        with self.assertRaises(ModelError):
            get_model("whatever")


class EndToEndTests(unittest.TestCase):
    def run_cli(self, argv, env=None):
        import run as runmod
        out = io.StringIO()
        with mock.patch.dict(os.environ, env or {}), contextlib.redirect_stdout(out):
            rc = runmod.main(argv)
        return rc, out.getvalue()

    def test_anthropic_run_against_fake_server_never_writes_key(self):
        ref = "```zehn\n" + c.read(c.DEMO_DIR, "ref.zehn") + "```\n"
        with FakeAPI([(200, ok_body(ref, 100, 50))]) as api, tempfile.TemporaryDirectory() as out:
            rc, text = self.run_cli(
                ["run", "--run-id", "api1", "--models", "anthropic:fake-model", "--yes", "--lang", "zehn",
                 "--repeats", "2", "--tasks-dir", c.DEMO_ROOT, "--out", out],
                {"ANTHROPIC_API_KEY": SENTINEL, "ANTHROPIC_BASE_URL": api.base})
            self.assertEqual(rc, 0, text)
            run_dir = os.path.join(out, "api1")
            recs = list(store.read_records(os.path.join(run_dir, "records.jsonl")))
            self.assertEqual(len(recs), 2)
            for r in recs:
                self.assertEqual(schema.validate_record(r), [])
                self.assertEqual((r["accepted_round"], r["total_in_tokens"], r["total_out_tokens"]), (1, 100, 50))
                self.assertEqual(r["model"], "anthropic:fake-model")
            for name in os.listdir(run_dir):
                with open(os.path.join(run_dir, name), encoding="utf-8") as f:
                    self.assertNotIn(SENTINEL, f.read(), name)
            meta = json.loads(c.read(run_dir, "meta.json"))
            self.assertEqual(meta["models"], ["anthropic:fake-model"])
            self.assertIn("zehn.py", meta["sources"])
            self.assertTrue(meta["python"])
            self.assertEqual(len(api.requests), 2)
            # an API run is not silently overwritten
            with self.assertRaises(SystemExit):
                self.run_cli(["run", "--run-id", "api1", "--models", "anthropic:fake-model", "--yes",
                              "--lang", "zehn", "--tasks-dir", c.DEMO_ROOT, "--out", out],
                             {"ANTHROPIC_API_KEY": SENTINEL, "ANTHROPIC_BASE_URL": api.base})

    def test_api_run_needs_yes(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(SystemExit):
                self.run_cli(["run", "--models", "anthropic:x", "--lang", "zehn", "--tasks-dir", c.DEMO_ROOT,
                              "--out", out], {"ANTHROPIC_API_KEY": SENTINEL})
            self.assertEqual(os.listdir(out), [])

    def test_dry_run_counts_without_key_or_network(self):
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:9"   # nothing listens there
        p = subprocess.run([sys.executable, os.path.join(c.BENCH, "run.py"), "run", "--models", "anthropic:x",
                            "--dry-run", "--lang", "zehn,python_plain", "--tasks-dir", c.DEMO_ROOT],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("runs: 10", p.stdout)
        self.assertIn("worst-case API calls: 50", p.stdout)

    def test_replay_and_stub_records(self):
        with tempfile.TemporaryDirectory() as out:
            rc, _ = self.run_cli(["replay", "--run-id", "rp", "--lang", "zehn,python_plain", "--repeats", "1",
                                  "--tasks-dir", c.DEMO_ROOT, "--out", out])
            self.assertEqual(rc, 0)
            recs = list(store.read_records(os.path.join(out, "rp", "records.jsonl")))
            self.assertEqual([r["accepted_round"] for r in recs], [1, 1])

    def test_verify_refs(self):
        rc, text = self.run_cli(["verify-refs", "--lang", "zehn,python_plain", "--tasks-dir", c.DEMO_ROOT])
        self.assertEqual(rc, 0, text)
        self.assertIn("OK   demo_000 zehn (8/8)", text)


if __name__ == "__main__":
    unittest.main()
