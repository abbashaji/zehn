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
  for (const x of readings) {
    const last: Run | undefined = runs[runs.length - 1];
    if (last !== undefined && last.value === x && last.count < limit) {
      last.count += 1;
    } else {
      runs.push({ value: x, count: 1 });
    }
  }
  return { ok: true, value: runs };
}
