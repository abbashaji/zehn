interface Account {
  owner: string;
  balance: number;
  overdraft: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function withdraw(acct: Account, amount: number): Result<Account> {
  if (amount <= 0) {
    return { ok: false, error: "amount must be positive" };
  }
  if (acct.balance - amount < -acct.overdraft) {
    return { ok: false, error: "insufficient funds" };
  }
  return { ok: true, value: { owner: acct.owner, balance: acct.balance - amount, overdraft: acct.overdraft } };
}
