type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function idle_time(starts: number[], ends: number[]): Result<number> {
  if (starts.length !== ends.length) {
    return { ok: false, error: "length mismatch" };
  }
  let prevStart = starts[0] ?? 0;
  let coverEnd = prevStart;
  let idle = 0;
  for (let i = 0; i < starts.length; i++) {
    const s = starts[i] ?? 0;
    const e = ends[i] ?? 0;
    if (e < s) {
      return { ok: false, error: "bad interval" };
    }
    if (s < prevStart) {
      return { ok: false, error: "unsorted" };
    }
    if (s > coverEnd) {
      idle += s - coverEnd;
    }
    coverEnd = Math.max(coverEnd, e);
    prevStart = s;
  }
  return { ok: true, value: idle };
}
