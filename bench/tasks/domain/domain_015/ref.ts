interface Summary {
  months: number;
  interest: number;
  paid: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function repayment_summary(principal: number, rate_bp: number, payment: number, max_months: number): Result<Summary> {
  if (principal <= 0) {
    return { ok: false, error: "invalid principal" };
  }
  if (rate_bp < 0) {
    return { ok: false, error: "invalid rate" };
  }
  if (payment <= 0) {
    return { ok: false, error: "invalid payment" };
  }
  if (max_months <= 0) {
    return { ok: false, error: "invalid term" };
  }
  const first = Math.floor((principal * rate_bp) / 10000);
  if (payment <= first) {
    return { ok: false, error: "payment too small: interest is " + first };
  }
  let balance = principal;
  let totalInterest = 0;
  let totalPaid = 0;
  for (let month = 1; month <= max_months; month++) {
    const interest = Math.floor((balance * rate_bp) / 10000);
    const owed = balance + interest;
    const pay = Math.min(payment, owed);
    balance = owed - pay;
    totalInterest += interest;
    totalPaid += pay;
    if (balance === 0) {
      return { ok: true, value: { months: month, interest: totalInterest, paid: totalPaid } };
    }
  }
  return { ok: false, error: "not repaid after " + max_months + " months: " + balance + " left" };
}
