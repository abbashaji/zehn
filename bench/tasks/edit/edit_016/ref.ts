type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function shipping_fee(grams: number): Result<number> {
  if (grams < 1) {
    return { ok: false, error: "invalid weight" };
  }
  if (grams <= 1000) {
    return { ok: true, value: 500 };
  }
  if (grams <= 5000) {
    return { ok: true, value: 900 };
  }
  return { ok: true, value: 1500 };
}
