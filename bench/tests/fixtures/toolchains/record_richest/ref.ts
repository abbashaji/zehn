interface Account {
  owner: string;
  balance: number;
  active: boolean;
}

function richest(accts: Account[]): Account | null {
  let best: Account | null = null;
  for (const a of accts) {
    if (best === null || a.balance > best.balance) {
      best = a;
    }
  }
  return best;
}
