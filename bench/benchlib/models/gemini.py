"""Google Gemini / Gemma client over the REST `generateContent` method (urllib only).

API facts read from Google's documentation on 2026-10-12 (https://ai.google.dev/api/generate-content):
  POST https://generativelanguage.googleapis.com/v1beta/models/<id>:generateContent?key=<key>
  body: system_instruction, contents[{role: user|model, parts[{text}]}], generationConfig{temperature,
  maxOutputTokens}; reply: candidates[].content.parts[].text, usageMetadata{promptTokenCount,
  candidatesTokenCount, thoughtsTokenCount, totalTokenCount}.
[UNVERIFIED against Google's pages] the finishReason value `MAX_TOKENS`, the `thought: true` flag on
reasoning parts and the 429 body layout: they are known from third-party documentation only.
Rate limits apply per Google *project*, not per key."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from . import ModelError, split_keys
from ._http import Scrubber, host_of, post_json

API_VERSION = "v1beta"
DEFAULT_BASE = "https://generativelanguage.googleapis.com/" + API_VERSION
DEFAULT_MAX_OUTPUT = 8192


class GeminiModel:
    kind = "gemini"

    def __init__(self, model_id: str, keys: List[str], base_url: Optional[str] = None,
                 max_output_tokens: int = DEFAULT_MAX_OUTPUT, timeout: float = 300.0):
        keys = split_keys(",".join(keys))
        if not keys:
            raise ModelError("GEMINI_API_KEYS is not set")
        self._keys = keys
        self.model_id = model_id
        self.name = "gemini:" + model_id
        self.base = (base_url or DEFAULT_BASE).rstrip("/")
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.scrub = Scrubber(keys)

    @classmethod
    def from_env(cls, model_id: str, **kwargs: Any) -> "GeminiModel":
        keys = split_keys(os.environ.get("GEMINI_API_KEYS", ""))
        base = os.environ.get("GEMINI_BASE_URL") or None   # test hook; leave unset for the real API
        return cls(model_id, keys, base_url=base, **kwargs)

    def __repr__(self) -> str:   # never show a key
        return "GeminiModel(%r, %d key(s))" % (self.model_id, len(self._keys))

    @property
    def key_ids(self) -> List[str]:
        return ["key#%d" % (i + 1) for i in range(len(self._keys))]

    @property
    def host(self) -> str:
        return host_of(self.base)

    def url(self) -> str:
        mid = self.model_id if self.model_id.startswith("models/") else "models/" + self.model_id
        return "%s/%s:generateContent" % (self.base, mid)

    def complete(self, system: str, messages: Any, temperature: float, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """One attempt on the first key (no scheduling)."""
        return self.complete_with_key(0, system, messages, temperature, ctx)

    def complete_with_key(self, key_index: int, system: str, messages: Any, temperature: float,
                          ctx: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "model" if m["role"] == "assistant" else "user",
                          "parts": [{"text": m["content"]}]} for m in messages],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": self.max_output_tokens},
        }
        key = self._keys[key_index]
        url = "%s?key=%s" % (self.url(), key)
        return self._parse(post_json(url, {}, payload, self.timeout, self.scrub))

    @staticmethod
    def _parse(data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            usage = data["usageMetadata"]
            in_tok = int(usage.get("promptTokenCount", 0))
            out_tok = int(usage.get("candidatesTokenCount", 0)) + int(usage.get("thoughtsTokenCount", 0))
            cands = data.get("candidates") or []
            text, finish = "", None
            if cands:
                cand = cands[0]
                finish = cand.get("finishReason")
                parts = (cand.get("content") or {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            return {"text": text, "in_tokens": in_tok, "out_tokens": out_tok,
                    "truncated": finish == "MAX_TOKENS"}
        except (KeyError, TypeError, ValueError, AttributeError) as ex:
            raise ModelError("unexpected response shape: %s: %s" % (type(ex).__name__, ex))
