from __future__ import annotations

import math
import random

DEFAULT_N = 10000
DEFAULT_SEED = 1234
DEFAULT_ALPHA = 0.05

NAN = float("nan")


def mean(values):
    vals = list(values)
    if not vals:
        return NAN
    return sum(vals) / len(vals)


def variance(values):
    """Population variance (divides by n). Empty input gives nan."""
    vals = list(values)
    if not vals:
        return NAN
    m = sum(vals) / len(vals)
    return sum((v - m) ** 2 for v in vals) / len(vals)


def diff(x, y):
    return x - y


def ratio(x, y):
    if y == 0 or y != y or x != x:
        return NAN
    return x / y


def percentile_interval(samples, alpha=DEFAULT_ALPHA):
    """Percentile interval of the finite samples; (nan, nan) when none."""
    s = sorted(v for v in samples if v == v)
    m = len(s)
    if m == 0:
        return (NAN, NAN)
    lo = s[min(m - 1, max(0, int(math.floor(alpha / 2.0 * m))))]
    hi = s[min(m - 1, max(0, int(math.ceil((1.0 - alpha / 2.0) * m)) - 1))]
    return (lo, hi)


def bootstrap_ci(values, stat=mean, n=DEFAULT_N, seed=DEFAULT_SEED, alpha=DEFAULT_ALPHA):
    """Percentile bootstrap CI of stat(values). Returns (lo, hi).

    Same inputs and seed give the same numbers (private random.Random).
    """
    vals = list(values)
    if not vals:
        return (NAN, NAN)
    rng = random.Random(seed)
    k = len(vals)
    out = []
    fast = stat is mean
    for _ in range(n):
        sample = rng.choices(vals, k=k)
        out.append(sum(sample) / k if fast else stat(sample))
    return percentile_interval(out, alpha)


def paired_bootstrap(a, b, combine=diff, reduce=mean, n=DEFAULT_N,
                     seed=DEFAULT_SEED, alpha=DEFAULT_ALPHA):
    """Paired bootstrap over tasks.

    a and b are aligned per-task values (one entry per task, same order).
    Each resample draws task indices once and applies them to both sides.
    The statistic is combine(reduce(a_sample), reduce(b_sample)).
    Returns (estimate, lo, hi).
    """
    if len(a) != len(b):
        raise ValueError("paired series must have the same length")
    k = len(a)
    if k == 0:
        return (NAN, NAN, NAN)
    est = combine(reduce(a), reduce(b))
    rng = random.Random(seed)
    idx_range = range(k)
    out = []
    for _ in range(n):
        idx = rng.choices(idx_range, k=k)
        out.append(combine(reduce([a[i] for i in idx]), reduce([b[i] for i in idx])))
    lo, hi = percentile_interval(out, alpha)
    return (est, lo, hi)


def paired_diff_ci(a, b, reduce=mean, n=DEFAULT_N, seed=DEFAULT_SEED, alpha=DEFAULT_ALPHA):
    """CI of reduce(a) - reduce(b) over paired tasks: (estimate, lo, hi)."""
    return paired_bootstrap(a, b, diff, reduce, n, seed, alpha)


def paired_ratio_ci(a, b, reduce=mean, n=DEFAULT_N, seed=DEFAULT_SEED, alpha=DEFAULT_ALPHA):
    """CI of reduce(a) / reduce(b) over paired tasks: (estimate, lo, hi).

    Resamples whose denominator is 0 are dropped.
    """
    return paired_bootstrap(a, b, ratio, reduce, n, seed, alpha)
