type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Account {
  id: number;
  balance: number;
}

function find_balance(accounts: Account[], id: number): number | null {
  for (const a of accounts) {
    if (a.id === id) {
      return a.balance;
    }
  }
  return null;
}

function transfer(accounts: Account[], from_id: number, to_id: number, amount: number): Result<Account[]> {
  if (amount <= 0) {
    return { ok: false, error: "invalid amount" };
  }
  const have = find_balance(accounts, from_id);
  if (have === null) {
    return { ok: false, error: "unknown source" };
  }
  if (find_balance(accounts, to_id) === null) {
    return { ok: false, error: "unknown destination" };
  }
  if (have <= amount) {
    return { ok: false, error: "insufficient funds" };
  }
  const updated = accounts.map((a): Account => {
    if (a.id === from_id) {
      return { id: a.id, balance: a.balance - amount };
    }
    if (a.id === to_id) {
      return { id: a.id, balance: a.balance + amount };
    }
    return a;
  });
  return { ok: true, value: updated };
}
