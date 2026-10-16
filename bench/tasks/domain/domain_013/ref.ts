interface Slot {
  denom: number;
  count: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function make_change(drawer: Slot[], amount: number): Result<Slot[]> {
  if (drawer.some((s) => s.denom <= 0 || s.count < 0)) {
    return { ok: false, error: "invalid drawer" };
  }
  if (amount <= 0) {
    return { ok: false, error: "invalid amount" };
  }
  let owed = amount;
  const updated: Slot[] = [];
  for (const slot of drawer) {
    const taken = Math.min(slot.count, Math.floor(owed / slot.denom));
    owed -= taken * slot.denom;
    updated.push({ denom: slot.denom, count: slot.count - taken });
  }
  if (owed > 0) {
    return { ok: false, error: "cannot make change: " + owed + " short" };
  }
  return { ok: true, value: updated };
}
