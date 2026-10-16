type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function started_hours(minutes: number): number {
  return Math.floor((minutes + 59) / 60);
}

function parking_fee(minutes: number, rate: number, grace: number, cap: number): Result<number> {
  if (minutes < 0) {
    return { ok: false, error: "invalid duration" };
  }
  if (rate < 0) {
    return { ok: false, error: "invalid rate" };
  }
  return { ok: true, value: started_hours(minutes) * rate };
}
