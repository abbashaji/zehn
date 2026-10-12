"""Shared single-attempt JSON POST for the remote clients (urllib only). Keys never leave this module
unscrubbed: every error text passes through `Scrubber`."""
from __future__ import annotations

import email.utils
import json
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from . import HttpError, ModelError, NetworkError


class Scrubber:
    """Replaces every key in a text by its label `key#N` (1-based, the order of the key list)."""

    def __init__(self, keys: List[str]):
        self._pairs = [(k, "key#%d" % (i + 1)) for i, k in enumerate(keys) if k]

    def __call__(self, text: str) -> str:
        for key, label in self._pairs:
            text = text.replace(key, label)
        return text


def parse_retry_after(header: Optional[str], body: str) -> Optional[float]:
    """Seconds to wait: the Retry-After header (seconds or HTTP date), else a `retryDelay": "12s"`
    field in the body (Google error details; not confirmed by Google's docs, so opportunistic)."""
    if header:
        header = header.strip()
        try:
            return max(0.0, float(header))
        except ValueError:
            try:
                when = email.utils.parsedate_to_datetime(header)
                return max(0.0, when.timestamp() - time.time())
            except (TypeError, ValueError):
                pass
    m = re.search(r'"retryDelay"\s*:\s*"([0-9.]+)s"', body)
    return float(m.group(1)) if m else None


_DAILY = re.compile(r"per\s*day|perday|daily|quota_exceeded", re.IGNORECASE)


def is_daily_quota(status: int, body: str) -> bool:
    """A 429 whose text points at a daily quota (Google's `quota_exceeded` code, 'per day' in the
    message). A heuristic: a wrong 'no' costs retries, a wrong 'yes' costs one key for this process."""
    return status == 429 and bool(_DAILY.search(body))


def host_of(url: str) -> str:
    return urlparse(url).netloc


def post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: float,
              scrub: Scrubber) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    hdrs = {"content-type": "application/json"}
    hdrs.update(headers)
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as ex:
        detail = scrub(ex.read().decode("utf-8", "replace"))[:600]
        raise HttpError(ex.code, detail, parse_retry_after(ex.headers.get("Retry-After"), detail))
    except (urllib.error.URLError, OSError) as ex:
        raise NetworkError(scrub("%s: %s" % (type(ex).__name__, ex)))
    try:
        data = json.loads(raw)
    except ValueError as ex:
        raise NetworkError("reply is not JSON: %s" % ex)
    if not isinstance(data, dict):
        raise ModelError("unexpected response shape: not an object")
    return data
