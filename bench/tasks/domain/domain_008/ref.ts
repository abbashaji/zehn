interface Loan {
  item: string;
  due_day: number;
  renewals: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function renew_loan(loan: Loan, today: number): Result<Loan> {
  if (today > loan.due_day) {
    return { ok: false, error: "overdue by " + (today - loan.due_day) + " days" };
  }
  if (loan.renewals >= 2) {
    return { ok: false, error: "renewal limit reached for " + loan.item };
  }
  if (today < loan.due_day - 3) {
    return { ok: false, error: "too early: renew from day " + (loan.due_day - 3) };
  }
  return { ok: true, value: { item: loan.item, due_day: loan.due_day + 14, renewals: loan.renewals + 1 } };
}
