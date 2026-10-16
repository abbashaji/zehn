type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Bracket {
  upto: number;
  rate: number;
}

function income_tax(income: number, brackets: Bracket[], top_rate: number): Result<number> {
  if (income < 0) {
    return { ok: false, error: "invalid income" };
  }
  let prev = 0;
  for (const b of brackets) {
    if (b.upto < prev) {
      return { ok: false, error: "invalid brackets" };
    }
    prev = b.upto;
  }
  if (top_rate < 0 || top_rate > 100 || brackets.some((b): boolean => b.rate < 0 || b.rate > 100)) {
    return { ok: false, error: "invalid rate" };
  }
  let total = 0;
  prev = 0;
  for (const b of brackets) {
    const slice = Math.max(0, Math.min(income, b.upto) - prev);
    total += slice * b.rate;
    prev = b.upto;
  }
  if (income > prev) {
    total += (income - prev) * top_rate;
  }
  return { ok: true, value: Math.floor(total / 100) };
}
