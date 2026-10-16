type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Loan {
  kind: string;
  days_late: number;
}

function daily_rate(kind: string): number | null {
  if (kind === "book") {
    return 10;
  }
  if (kind === "dvd") {
    return 50;
  }
  if (kind === "game") {
    return 100;
  }
  return null;
}

function total_fine(loans: Loan[], member: boolean): Result<number> {
  let total = 0;
  for (const loan of loans) {
    const rate = daily_rate(loan.kind);
    if (rate === null) {
      return { ok: false, error: "unknown kind" };
    }
    if (loan.days_late < 0) {
      return { ok: false, error: "invalid days" };
    }
    let days = loan.days_late;
    if (member) {
      days = Math.max(0, days - 3);
    }
    total += Math.min(days * rate, 1500);
  }
  return { ok: true, value: Math.min(total, 4000) };
}
