type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function band_tax(income: number, lower: number, upper: number, percent: number): number {
  const top = Math.min(income, upper);
  if (top <= lower) {
    return 0;
  }
  return Math.floor(((top - lower) * percent) / 100);
}

function income_tax(income: number, children: number): Result<number> {
  if (income < 0) {
    return { ok: false, error: "invalid income" };
  }
  if (children < 0) {
    return { ok: false, error: "invalid children" };
  }
  const gross =
    band_tax(income, 10000, 30000, 15) +
    band_tax(income, 30000, 70000, 30) +
    band_tax(income, 70000, income, 45);
  return { ok: true, value: Math.max(0, gross - 300 * children) };
}
