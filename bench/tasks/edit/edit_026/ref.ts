type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function started_hours(minutes: number): number {
  return Math.floor((minutes + 59) / 60);
}

function block_fee(minutes: number, rate: number, cap: number): number {
  return Math.min(started_hours(minutes) * rate, cap);
}

function parking_fee(minutes: number, rate: number, grace: number, cap: number): Result<number> {
  if (minutes < 0) {
    return { ok: false, error: "invalid duration" };
  }
  if (rate < 0) {
    return { ok: false, error: "invalid rate" };
  }
  if (grace < 0 || cap < 0) {
    return { ok: false, error: "invalid limit" };
  }
  if (minutes <= grace) {
    return { ok: true, value: 0 };
  }
  const days = Math.floor(minutes / 1440);
  const rest = minutes % 1440;
  return { ok: true, value: days * Math.min(24 * rate, cap) + block_fee(rest, rate, cap) };
}
