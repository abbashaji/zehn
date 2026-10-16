type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Rate {
  base: number;
  extra: number;
  limit: number;
}

function rateFor(zone: string): Rate | null {
  if (zone === "local") {
    return { base: 300, extra: 50, limit: 30000 };
  }
  if (zone === "national") {
    return { base: 500, extra: 100, limit: 30000 };
  }
  if (zone === "international") {
    return { base: 1500, extra: 400, limit: 20000 };
  }
  return null;
}

function parcel_fee(zone: string, grams: number): Result<number> {
  if (grams <= 0) {
    return { ok: false, error: "invalid weight" };
  }
  const rate = rateFor(zone);
  if (rate === null) {
    return { ok: false, error: "unknown zone: " + zone };
  }
  if (grams > rate.limit) {
    return { ok: false, error: "too heavy for " + zone + ": limit is " + rate.limit + " g" };
  }
  const kilos = Math.floor((grams + 999) / 1000);
  return { ok: true, value: rate.base + (kilos - 1) * rate.extra };
}
