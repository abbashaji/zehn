type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function flat_rate(income: number): number {
  if (income <= 10000) {
    return 0;
  }
  if (income <= 30000) {
    return 15;
  }
  if (income <= 70000) {
    return 30;
  }
  return 45;
}

function income_tax(income: number, children: number): Result<number> {
  if (income < 0) {
    return { ok: false, error: "invalid income" };
  }
  if (children < 0) {
    return { ok: false, error: "invalid children" };
  }
  return { ok: true, value: Math.floor((income * flat_rate(income)) / 100) - 300 * children };
}
