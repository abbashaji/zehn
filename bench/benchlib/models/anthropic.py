"""Anthropic Messages API client over urllib (stdlib only). The key comes from env ANTHROPIC_API_KEY
and is never written anywhere.

[UNVERIFIED] The endpoint path, the headers (x-api-key, anthropic-version) and the request/response
field names below are written from memory. Check them against Anthropic's API documentation before
relying on this client."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional

from . import ModelError

DEFAULT_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"   # [UNVERIFIED]
MAX_TOKENS = 4096
RETRY_STATUS = (429, 500, 502, 503, 504, 529)


class AnthropicModel:
    def __init__(self, model_id: str, url: Optional[str] = None, api_key: Optional[str] = None,
                 max_attempts: int = 6, sleep: Callable[[float], None] = time.sleep, timeout: float = 120.0):
        key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ModelError("ANTHROPIC_API_KEY is not set")
        self._key = key
        self.model_id = model_id
        self.name = "anthropic:" + model_id
        if url:
            self.url = url
        elif os.environ.get("ANTHROPIC_BASE_URL"):
            self.url = os.environ["ANTHROPIC_BASE_URL"].rstrip("/") + "/v1/messages"
        else:
            self.url = DEFAULT_URL
        self.max_attempts = max_attempts
        self._sleep = sleep
        self.timeout = timeout

    def __repr__(self) -> str:   # never show the key
        return "AnthropicModel(%r)" % self.model_id

    def complete(self, system: str, messages: Any, temperature: float, ctx: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps({"model": self.model_id, "max_tokens": MAX_TOKENS, "temperature": temperature,
                           "system": system, "messages": list(messages)}).encode("utf-8")
        headers = {"content-type": "application/json", "x-api-key": self._key,
                   "anthropic-version": API_VERSION}
        delay = 1.0
        last = "no attempt made"
        for attempt in range(1, self.max_attempts + 1):
            req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                return self._parse(data)
            except urllib.error.HTTPError as ex:
                detail = ex.read().decode("utf-8", "replace")[:300]
                last = "HTTP %d: %s" % (ex.code, detail)
                if ex.code not in RETRY_STATUS:
                    raise ModelError(last)
            except (urllib.error.URLError, OSError, ValueError) as ex:
                last = "%s: %s" % (type(ex).__name__, ex)
            if attempt < self.max_attempts:
                self._sleep(delay)
                delay = min(delay * 2, 60.0)
        raise ModelError("giving up after %d attempts (%s)" % (self.max_attempts, last))

    @staticmethod
    def _parse(data: Any) -> Dict[str, Any]:
        try:
            text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
            usage = data["usage"]
            return {"text": text, "in_tokens": int(usage["input_tokens"]),
                    "out_tokens": int(usage["output_tokens"])}
        except (KeyError, TypeError, ValueError) as ex:
            raise ModelError("unexpected response shape: %s" % ex)
