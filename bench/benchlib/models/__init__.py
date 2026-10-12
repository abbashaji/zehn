"""Model clients. A client has `.name` and
`complete(system, messages, temperature, ctx) -> {"text", "in_tokens", "out_tokens"}`
(remote clients may add `"truncated": bool`).
`ctx` = {"task", "lang", "ext", "round", "ref_code"} is for the scripted stubs; real clients ignore it.

Remote clients (`gemini:`, `openai:`) make exactly one HTTP attempt per call and raise HttpError /
NetworkError; retries, rate limits and key rotation belong to `scheduler.py`."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ModelError(Exception):
    """A model call that failed for good (after retries)."""


class HttpError(ModelError):
    """One HTTP attempt answered with an error status. `body` is already scrubbed of keys."""

    def __init__(self, status: int, body: str, retry_after: Optional[float] = None):
        super().__init__("HTTP %d: %s" % (status, body))
        self.status = status
        self.body = body
        self.retry_after = retry_after


class NetworkError(ModelError):
    """One HTTP attempt failed before any status came back (timeout, refused, bad JSON)."""


class RunAborted(Exception):
    """Raised through the loop: the run must not be recorded (the scheduler requeues it)."""


class KeyExhausted(RunAborted):
    """This key has no quota left for this process."""


class FatalModelError(RunAborted):
    """A non-transient refusal (bad request, bad key, unknown model): retrying cannot help."""


def split_keys(text: str) -> List[str]:
    """Comma-separated keys -> list, blanks dropped, duplicates dropped (a repeated key would only
    double the request rate on one quota)."""
    out: List[str] = []
    for part in (text or "").split(","):
        part = part.strip()
        if part and part not in out:
            out.append(part)
    return out


REMOTE_KINDS = ("gemini", "openai")


def get_model(spec: str, **kwargs: Any) -> Any:
    """`stub:perfect`, `stub:broken_then_fixed`, `stub:never_valid`, `anthropic:<model-id>`,
    `gemini:<model-id>`, `openai:<model-id>`."""
    kind, _, rest = spec.partition(":")
    if not rest:
        raise ModelError("model must look like stub:<name>, anthropic:<model-id>, gemini:<model-id> "
                         "or openai:<model-id>, got %r" % spec)
    if kind == "stub":
        from .stub import StubModel
        return StubModel(rest)
    if kind == "anthropic":
        from .anthropic import AnthropicModel
        return AnthropicModel(rest)
    if kind == "gemini":
        from .gemini import GeminiModel
        return GeminiModel.from_env(rest, **kwargs)
    if kind == "openai":
        from .openai_compat import OpenAICompatModel
        return OpenAICompatModel.from_env(rest, **kwargs)
    raise ModelError("unknown model kind %r in %r" % (kind, spec))


def is_remote_model(spec: str) -> bool:
    """Free-tier remote models, run through the rate-limit scheduler."""
    return spec.partition(":")[0] in REMOTE_KINDS


def is_api_model(spec: str) -> bool:
    """Any model that calls a network API (needs --yes)."""
    return spec.startswith("anthropic:") or is_remote_model(spec)


Messages = List[Dict[str, str]]
