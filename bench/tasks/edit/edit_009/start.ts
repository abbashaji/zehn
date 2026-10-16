type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Run {
  value: number;
  count: number;
}

function compress(readings: number[], limit: number): Result<Run[]> {
  if (limit < 1) {
    return { ok: false, error: "invalid limit" };
  }
  const runs: Run[] = [];
  let value = 0;
  let count = 0;
  for (const x of readings) {
    if (count > 0 && x === value && count <= limit) {
      count += 1;
    } else {
      if (count > 0) {
        runs.push({ value, count });
      }
      value = x;
      count = 1;
    }
  }
  if (count > 1) {
    runs.push({ value, count });
  }
  return { ok: true, value: runs };
}
