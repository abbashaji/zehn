from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def retry_log(outcomes: List[bool], max_attempts: int, base: int) -> Result[int]:
    if max_attempts < 1:
        return Err("no attempts allowed")
    wait = min(base, 60)
    for attempt in range(1, max_attempts + 1):
        if attempt <= len(outcomes) and outcomes[attempt - 1]:
            print(f"attempt {attempt}: ok")
            return Ok(attempt)
        print(f"attempt {attempt}: failed")
        if attempt < max_attempts:
            print(f"waiting {wait}")
            wait = min(wait * 2, 60)
    return Err(f"gave up after {max_attempts} attempts")
