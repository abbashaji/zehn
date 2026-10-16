type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function parking_fee(minutes: number, rate: number, daily_cap: number): Result<number> {
  if (minutes < 0) {
    return { ok: false, error: "invalid minutes" };
  }
  if (rate < 1) {
    return { ok: false, error: "invalid rate" };
  }
  return { ok: true, value: Math.floor((minutes + 59) / 60) * rate };
}
