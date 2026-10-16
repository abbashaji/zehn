from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Job:
    id: int
    burst: int


def finish_order(jobs: List[Job], quantum: int) -> Result[List[int]]:
    if quantum <= 0:
        return Err("invalid quantum")
    for job in jobs:
        if job.burst <= 0:
            return Err("invalid burst")
    queue: List[Job] = list(jobs)
    done: List[int] = []
    while queue:
        job = queue.pop(0)
        if job.burst <= quantum:
            done.append(job.id)
        else:
            queue.append(Job(job.id, job.burst - quantum))
    return Ok(done)
