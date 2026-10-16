type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function tariff_bill(limits: number[], rates: number[], usage: number): Result<number> {
  if (limits.length !== rates.length) {
    return { ok: false, error: "length mismatch" };
  }
  const lastLimit = limits[limits.length - 1];
  if (lastLimit === undefined) {
    return { ok: false, error: "no tiers" };
  }
  let prev = 0;
  for (const limit of limits) {
    if (limit <= prev) {
      return { ok: false, error: "bad limits" };
    }
    prev = limit;
  }
  if (rates.some((r) => r < 0)) {
    return { ok: false, error: "bad rate" };
  }
  if (usage < 0) {
    return { ok: false, error: "negative usage" };
  }
  if (usage > lastLimit) {
    return { ok: false, error: "usage above last tier" };
  }
  let total = 0;
  prev = 0;
  for (let i = 0; i < limits.length; i++) {
    const limit = limits[i] ?? 0;
    const rate = rates[i] ?? 0;
    total += Math.max(0, Math.min(usage, limit) - prev) * rate;
    prev = limit;
  }
  return { ok: true, value: total };
}
