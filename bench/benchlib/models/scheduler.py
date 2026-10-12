"""Client-side rate limiting for the free remote models, and the worker pool that runs the work list.

What it guarantees (and what it does not):
- Before every HTTP attempt a key's worker waits until the attempt fits inside `margin` (default 0.9) of
  that key's requests-per-minute and tokens-per-minute (sliding 60 s windows) and requests-per-day
  (a persistent counter per key and UTC date). Retries count as attempts.
- It cannot know the provider's real limits or when the provider's day resets (Google's reset at midnight
  Pacific; the counter here follows the UTC date), so a 429 can still happen; it is handled (backoff, or
  the key is marked exhausted for this process when the 429 names a daily quota).
- One worker per key; every key is for the same model. There is no failover to another model."""
from __future__ import annotations

import collections
import datetime
import json
import math
import os
import random
import threading
import time
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

from . import (FatalModelError, HttpError, KeyExhausted, ModelError, NetworkError, RunAborted)
from ._http import is_daily_quota

MAX_TRIES = 6
MAX_RETRY_AFTER = 3600.0
CHARS_PER_TOKEN = 3.5


class Clock:
    """Monotonic clock with a test hook: `scale` > 1 makes time run that many times faster
    (sleeps shrink, `now()` grows), so a 60 s window can be tested in a second."""

    def __init__(self, scale: float = 1.0):
        self.scale = scale if scale > 0 else 1.0

    def now(self) -> float:
        return time.monotonic() * self.scale

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds / self.scale)

    def utc_date(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


# ----------------------------------------------------------------------------- limits

def load_limits(path: str) -> Dict[str, Dict[str, Optional[int]]]:
    """bench/limits.json: model spec -> {"rpm", "tpm", "rpd"} per key. Keys starting with `_` are notes."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_") and isinstance(v, dict)}


def resolve_limits(spec: str, table: Dict[str, Dict[str, Optional[int]]],
                   overrides: Dict[str, Optional[int]]) -> Dict[str, int]:
    """Per-field: a command-line override wins, else the table. A field that is missing or null in both
    makes the model unusable (ModelError): limits are never guessed."""
    entry = table.get(spec, {})
    out: Dict[str, int] = {}
    missing = []
    for field in ("rpm", "tpm", "rpd"):
        val = overrides.get(field)
        if val is None:
            val = entry.get(field)
        if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
            missing.append(field)
        else:
            out[field] = val
    if missing:
        raise ModelError("no usable limits for %s (missing: %s): add them to bench/limits.json or pass "
                         "--%s" % (spec, ", ".join(missing), "/--".join(missing)))
    return out


# ----------------------------------------------------------------------------- day counter

class QuotaState:
    """Requests sent per key id and UTC date, saved in `<run dir>/quota_state.json` (no keys in it)."""

    def __init__(self, path: Optional[str], clock: Clock):
        self.path = path
        self.clock = clock
        self._lock = threading.Lock()
        self._days: Dict[str, Dict[str, int]] = {}
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    days = json.load(f).get("days", {})
                self._days = {d: {k: int(v) for k, v in c.items()} for d, c in days.items()}
            except (ValueError, OSError, AttributeError, TypeError):
                self._days = {}   # unreadable state: start counting from zero (the 429 path still protects)

    def count(self, key_id: str) -> int:
        with self._lock:
            return self._days.get(self.clock.utc_date(), {}).get(key_id, 0)

    def add(self, key_id: str) -> None:
        with self._lock:
            today = self.clock.utc_date()
            day = self._days.setdefault(today, {})
            day[key_id] = day.get(key_id, 0) + 1
            for old in sorted(self._days)[:-7]:
                del self._days[old]
            self._save()

    def _save(self) -> None:
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"schema": 1, "days": self._days}, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, self.path)


# ----------------------------------------------------------------------------- one key

class KeyLimiter:
    """Sliding-window limiter for one key. `acquire` blocks; `settle` corrects the token estimate."""

    def __init__(self, key_id: str, rpm: int, tpm: int, rpd: int, margin: float, clock: Clock,
                 quota: QuotaState):
        self.key_id = key_id
        self.max_rpm = max(1, int(rpm * margin))
        self.max_tpm = max(1, int(tpm * margin))
        self.max_rpd = max(1, int(rpd * margin))
        self.clock = clock
        self.quota = quota
        self._events: Deque[List[float]] = collections.deque()   # [time, tokens]
        self._lock = threading.Lock()

    def acquire(self, est_tokens: int) -> List[float]:
        while True:
            with self._lock:
                now = self.clock.now()
                while self._events and self._events[0][0] <= now - 60.0:
                    self._events.popleft()
                if self.quota.count(self.key_id) >= self.max_rpd:
                    raise KeyExhausted("%s: local daily budget of %d requests used" % (self.key_id, self.max_rpd))
                wait = 0.0
                if len(self._events) >= self.max_rpm:
                    wait = max(wait, self._events[0][0] + 60.0 - now)
                used = sum(e[1] for e in self._events)
                if self._events and used + est_tokens > self.max_tpm:
                    need, acc = used + est_tokens - self.max_tpm, 0.0
                    for t, tok in self._events:
                        acc += tok
                        if acc >= need:
                            wait = max(wait, t + 60.0 - now)
                            break
                if wait <= 0.0:
                    entry = [now, float(est_tokens)]
                    self._events.append(entry)
                    self.quota.add(self.key_id)
                    return entry
            self.clock.sleep(wait + 0.05)

    def settle(self, entry: List[float], actual_tokens: int) -> None:
        with self._lock:
            entry[1] = float(actual_tokens)


def estimate_tokens(system: str, messages: Any, expected_output: int) -> int:
    chars = len(system) + sum(len(m["content"]) for m in messages)
    return int(math.ceil(chars / CHARS_PER_TOKEN)) + expected_output


class KeyClient:
    """What the loop sees for one key: `.name` and `.complete`. Adds limiting, retries and the
    exhausted state around `model.complete_with_key`."""

    def __init__(self, model: Any, key_index: int, limiter: KeyLimiter, expected_output: int,
                 clock: Clock, rng: Optional[random.Random] = None, log: Callable[[str], None] = print):
        self.model = model
        self.name = model.name
        self.key_index = key_index
        self.key_id = limiter.key_id
        self.limiter = limiter
        self.expected_output = expected_output
        self.clock = clock
        self.rng = rng or random.Random()
        self.log = log
        self.exhausted = False

    def _backoff(self, attempt: int) -> float:
        return min(60.0, 2.0 * (2 ** (attempt - 1))) * self.rng.uniform(0.5, 1.0)

    def complete(self, system: str, messages: Any, temperature: float, ctx: Dict[str, Any]) -> Dict[str, Any]:
        est = estimate_tokens(system, messages, self.expected_output)
        last = "no attempt made"
        for attempt in range(1, MAX_TRIES + 1):
            try:
                entry = self.limiter.acquire(est)
            except KeyExhausted:
                self.exhausted = True
                raise
            try:
                reply = self.model.complete_with_key(self.key_index, system, messages, temperature, ctx)
            except HttpError as ex:
                last = "%s (%s)" % (ex, self.key_id)
                if ex.status == 429 and is_daily_quota(ex.status, ex.body):
                    self.exhausted = True
                    raise KeyExhausted("%s: daily quota reached (%s)" % (self.key_id, ex.body[:200]))
                if ex.status not in (429, 500, 502, 503, 504):
                    raise FatalModelError("%s: HTTP %d: %s" % (self.key_id, ex.status, ex.body[:300]))
                delay = min(ex.retry_after, MAX_RETRY_AFTER) if ex.retry_after is not None \
                    else self._backoff(attempt)
            except NetworkError as ex:
                last = "%s (%s)" % (ex, self.key_id)
                delay = self._backoff(attempt)
            else:
                self.limiter.settle(entry, reply["in_tokens"] + reply["out_tokens"])
                return reply
            if attempt < MAX_TRIES:
                self.log("retry %d/%d on %s in %.1fs: %s" % (attempt, MAX_TRIES - 1, self.key_id, delay, last[:120]))
                self.clock.sleep(delay)
        raise ModelError("giving up after %d attempts (%s)" % (MAX_TRIES, last))


def build_key_clients(model: Any, limits: Dict[str, int], margin: float, expected_output: int,
                      clock: Clock, quota: QuotaState, log: Callable[[str], None] = print,
                      rng: Optional[random.Random] = None) -> List[KeyClient]:
    out = []
    for i, key_id in enumerate(model.key_ids):
        lim = KeyLimiter(key_id, limits["rpm"], limits["tpm"], limits["rpd"], margin, clock, quota)
        out.append(KeyClient(model, i, lim, expected_output, clock, rng, log))
    return out


# ----------------------------------------------------------------------------- worker pool

class PoolResult:
    def __init__(self) -> None:
        self.remaining: List[Any] = []
        self.done = 0
        self.budget_reached = False
        self.fatal: Optional[str] = None


def run_pool(items: List[Any], clients: List[Any], execute: Callable[[Any, Any], Any],
             on_record: Callable[[Any], None], clock: Clock, budget_minutes: Optional[float] = None,
             log: Callable[[str], None] = print) -> PoolResult:
    """One thread per client. A worker takes the next item and runs it entirely on its own client. An item
    interrupted by KeyExhausted goes back to the front of the queue and that worker stops. After
    `budget_minutes` no new item is started; running ones finish."""
    cond = threading.Condition()
    queue: Deque[Any] = collections.deque(items)
    res = PoolResult()
    state = {"inflight": 0}
    deadline = clock.now() + budget_minutes * 60.0 if budget_minutes is not None else None

    def worker(client: Any) -> None:
        while True:
            with cond:
                while True:
                    if res.fatal:
                        return
                    if deadline is not None and clock.now() >= deadline:
                        if queue:
                            res.budget_reached = True
                        return
                    if queue:
                        item = queue.popleft()
                        state["inflight"] += 1
                        break
                    if state["inflight"] == 0:
                        return
                    cond.wait(timeout=0.5)
            try:
                rec = execute(item, client)
                on_record(rec)
            except KeyExhausted as ex:
                with cond:
                    queue.appendleft(item)
                    state["inflight"] -= 1
                    cond.notify_all()
                log("KEY_EXHAUSTED %s" % ex)
                return
            except RunAborted as ex:
                with cond:
                    queue.appendleft(item)
                    state["inflight"] -= 1
                    res.fatal = str(ex)
                    cond.notify_all()
                return
            except Exception as ex:   # noqa: BLE001 - a bug must stop the process, not loop
                with cond:
                    queue.appendleft(item)
                    state["inflight"] -= 1
                    res.fatal = "internal error: %s: %s" % (type(ex).__name__, ex)
                    cond.notify_all()
                return
            with cond:
                state["inflight"] -= 1
                res.done += 1
                cond.notify_all()

    threads = [threading.Thread(target=worker, args=(c,), daemon=True) for c in clients]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    res.remaining = list(queue)
    return res
