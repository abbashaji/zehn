type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Loan {
  id: number;
  due: number;
  renewals: number;
}

function find_loan(loans: Loan[], id: number): Loan | null {
  for (const loan of loans) {
    if (loan.id === id) {
      return loan;
    }
  }
  return null;
}

function renew(loans: Loan[], id: number, today: number, reserved: number[], max_renewals: number): Result<Loan[]> {
  const loan = find_loan(loans, id);
  if (loan === null) {
    return { ok: false, error: "unknown loan" };
  }
  const updated = loans.map((x): Loan => (x.id === id ? { id: x.id, due: x.due + 14, renewals: x.renewals + 1 } : x));
  return { ok: true, value: updated };
}
