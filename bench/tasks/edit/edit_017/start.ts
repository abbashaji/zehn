type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function days_in_month(year: number, month: number): Result<number> {
  if (month < 1 || month > 12) {
    return { ok: false, error: "invalid month" };
  }
  if (month === 2) {
    return { ok: true, value: 28 };
  }
  if (month === 4 || month === 6 || month === 9 || month === 11) {
    return { ok: true, value: 30 };
  }
  return { ok: true, value: 31 };
}
