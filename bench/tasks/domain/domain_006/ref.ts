interface Stock {
  sku: string;
  on_hand: number;
  reserved: number;
}

interface Order {
  sku: string;
  qty: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function reserve_orders(stock: Stock[], orders: Order[]): Result<Stock[]> {
  const lines: Stock[] = stock.map((s) => ({ sku: s.sku, on_hand: s.on_hand, reserved: s.reserved }));
  for (const order of orders) {
    if (order.qty <= 0) {
      return { ok: false, error: "invalid quantity for " + order.sku };
    }
    const line = lines.find((s) => s.sku === order.sku);
    if (line === undefined) {
      return { ok: false, error: "unknown sku: " + order.sku };
    }
    const available = line.on_hand - line.reserved;
    if (available < order.qty) {
      return {
        ok: false,
        error: "cannot reserve " + order.qty + " of " + order.sku + ": only " + available + " available",
      };
    }
    line.reserved += order.qty;
  }
  return { ok: true, value: lines };
}
