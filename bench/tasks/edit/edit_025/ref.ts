type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function is_leap(year: number): boolean {
  if (year % 400 === 0) {
    return true;
  }
  if (year % 100 === 0) {
    return false;
  }
  return year % 4 === 0;
}

function days_in_month(month: number, year: number): Result<number> {
  if (month < 1 || month > 12) {
    return { ok: false, error: "invalid month" };
  }
  if (year < 1) {
    return { ok: false, error: "invalid year" };
  }
  if (month === 2) {
    if (is_leap(year)) {
      return { ok: true, value: 29 };
    }
    return { ok: true, value: 28 };
  }
  if (month === 4 || month === 6 || month === 9 || month === 11) {
    return { ok: true, value: 30 };
  }
  return { ok: true, value: 31 };
}
