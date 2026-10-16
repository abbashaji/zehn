interface Card {
  id: string;
  balance: number;
  expires: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function pay_bill(cards: Card[], bill: number, today: number): Result<Card[]> {
  if (bill <= 0) {
    return { ok: false, error: "invalid bill" };
  }
  const isUsable = (c: Card): boolean => c.balance > 0 && c.expires >= today;
  const total = cards.filter(isUsable).reduce((sum, c) => sum + c.balance, 0);
  if (total < bill) {
    return { ok: false, error: "short by " + (bill - total) };
  }
  let owed = bill;
  let used = 0;
  const updated: Card[] = [];
  for (const card of cards) {
    if (owed > 0 && isUsable(card)) {
      const paid = Math.min(card.balance, owed);
      owed -= paid;
      used += 1;
      updated.push({ id: card.id, balance: card.balance - paid, expires: card.expires });
    } else {
      updated.push({ id: card.id, balance: card.balance, expires: card.expires });
    }
  }
  if (used > 3) {
    return { ok: false, error: "too many cards: needs " + used };
  }
  return { ok: true, value: updated };
}
