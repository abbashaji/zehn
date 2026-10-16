type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function parking_fee(minutes: number, rate: number, daily_cap: number): Result<number> {
  if (minutes < 0) {
    return { ok: false, error: "invalid minutes" };
  }
  if (rate < 1) {
    return { ok: false, error: "invalid rate" };
  }
  if (daily_cap < 1) {
    return { ok: false, error: "invalid cap" };
  }
  if (minutes <= 15) {
    return { ok: true, value: 0 };
  }
  const blockCost = Math.min(24 * rate, daily_cap);
  const rest = minutes % 1440;
  const partial = Math.min(Math.floor((rest + 59) / 60) * rate, daily_cap);
  return { ok: true, value: Math.floor(minutes / 1440) * blockCost + partial };
}
