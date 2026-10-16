type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function moving_sum(values: number[], window: number): Result<number[]> {
  if (window < 1) {
    return { ok: false, error: "invalid window" };
  }
  const sums: number[] = [];
  for (let i = 0; i < values.length; i++) {
    const lo = Math.max(0, i - window + 1);
    let total = 0;
    for (let j = lo; j <= i; j++) {
      total += values[j] ?? 0;
    }
    sums.push(total);
  }
  return { ok: true, value: sums };
}
