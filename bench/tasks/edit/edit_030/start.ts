type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Job {
  id: number;
  burst: number;
}

function finish_order(jobs: Job[], quantum: number): Result<number[]> {
  if (quantum <= 0) {
    return { ok: false, error: "invalid quantum" };
  }
  const queue: Job[] = [...jobs];
  const done: number[] = [];
  for (;;) {
    const job = queue.shift();
    if (job === undefined) {
      break;
    }
    if (job.burst < quantum) {
      done.push(job.id);
    } else {
      queue.push({ id: job.id, burst: job.burst - quantum });
    }
  }
  return { ok: true, value: done };
}
