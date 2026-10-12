"""OpenAI-compatible chat client (Groq, GitHub Models, Ollama, ...): POST <base>/chat/completions with a
bearer key, a system message, `temperature`, `max_tokens`; tokens come from `usage`.
Keys: env OPENAI_COMPAT_API_KEYS (comma list); base: env OPENAI_COMPAT_BASE_URL.
[UNVERIFIED] the layout is the widely used chat-completions one, written from memory; it was not
checked against each provider's own documentation."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from . import ModelError, split_keys
from ._http import Scrubber, host_of, post_json

DEFAULT_MAX_OUTPUT = 8192


class OpenAICompatModel:
    kind = "openai"

    def __init__(self, model_id: str, keys: List[str], base_url: Optional[str] = None,
                 max_output_tokens: int = DEFAULT_MAX_OUTPUT, timeout: float = 300.0):
        keys = split_keys(",".join(keys))
        if not keys:
            raise ModelError("OPENAI_COMPAT_API_KEYS is not set")
        if not base_url:
            raise ModelError("OPENAI_COMPAT_BASE_URL is not set")
        self._keys = keys
        self.model_id = model_id
        self.name = "openai:" + model_id
        self.base = base_url.rstrip("/")
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.scrub = Scrubber(keys)

    @classmethod
    def from_env(cls, model_id: str, **kwargs: Any) -> "OpenAICompatModel":
        keys = split_keys(os.environ.get("OPENAI_COMPAT_API_KEYS", ""))
        return cls(model_id, keys, base_url=os.environ.get("OPENAI_COMPAT_BASE_URL") or None, **kwargs)

    def __repr__(self) -> str:
        return "OpenAICompatModel(%r, %d key(s))" % (self.model_id, len(self._keys))

    @property
    def key_ids(self) -> List[str]:
        return ["key#%d" % (i + 1) for i in range(len(self._keys))]

    @property
    def host(self) -> str:
        return host_of(self.base)

    def complete(self, system: str, messages: Any, temperature: float, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return self.complete_with_key(0, system, messages, temperature, ctx)

    def complete_with_key(self, key_index: int, system: str, messages: Any, temperature: float,
                          ctx: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"model": self.model_id, "temperature": temperature, "max_tokens": self.max_output_tokens,
                   "messages": [{"role": "system", "content": system}] + [dict(m) for m in messages]}
        headers = {"authorization": "Bearer " + self._keys[key_index]}
        return self._parse(post_json(self.base + "/chat/completions", headers, payload, self.timeout, self.scrub))

    @staticmethod
    def _parse(data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            usage = data["usage"]
            choice = (data.get("choices") or [{}])[0]
            text = (choice.get("message") or {}).get("content") or ""
            return {"text": text, "in_tokens": int(usage["prompt_tokens"]),
                    "out_tokens": int(usage["completion_tokens"]),
                    "truncated": choice.get("finish_reason") == "length"}
        except (KeyError, TypeError, ValueError, IndexError, AttributeError) as ex:
            raise ModelError("unexpected response shape: %s: %s" % (type(ex).__name__, ex))
