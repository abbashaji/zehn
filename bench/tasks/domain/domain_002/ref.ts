interface Item {
  name: string;
  qty: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function remove_stock(items: Item[], name: string, qty: number): Result<Item[]> {
  if (qty <= 0) {
    return { ok: false, error: "quantity must be positive" };
  }
  const found = items.find((it) => it.name === name);
  if (found === undefined) {
    return { ok: false, error: "unknown item: " + name };
  }
  if (found.qty < qty) {
    return { ok: false, error: "insufficient stock for " + name + ": have " + found.qty + ", need " + qty };
  }
  const updated = items.map((it) => (it.name === name ? { name: it.name, qty: it.qty - qty } : it));
  return { ok: true, value: updated };
}
