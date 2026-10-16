type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function moving_sum(values: number[], window: number): Result<number[]> {
  const sums: number[] = [];
  let total = 0;
  for (const v of values) {
    total += v;
    sums.push(total);
  }
  return { ok: true, value: sums };
}
