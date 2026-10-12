type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function ticket_price(age: number): Result<number> {
  if (age < 0) {
    return { ok: false, error: "invalid age" };
  }
  if (age < 5) {
    return { ok: true, value: 0 };
  }
  if (age < 18) {
    return { ok: true, value: 800 };
  }
  if (age <= 65) {
    return { ok: true, value: 1500 };
  }
  return { ok: true, value: 1000 };
}
