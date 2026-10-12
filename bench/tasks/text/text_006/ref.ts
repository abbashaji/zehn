type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Item {
  name: string;
  qty: number;
  cents: number;
}

function money(c: number): string {
  const rem = c % 100;
  const pad = rem < 10 ? "0" + String(rem) : String(rem);
  return String(Math.floor(c / 100)) + "." + pad;
}

function invoice(items: Item[]): Result<string> {
  const lines: string[] = [];
  let total = 0;
  for (const it of items) {
    if (it.qty <= 0 || it.cents < 0) {
      return { ok: false, error: "invalid item: " + it.name };
    }
    const amount = it.qty * it.cents;
    total += amount;
    lines.push(it.name + " x" + String(it.qty) + " @ " + money(it.cents) + " = " + money(amount));
  }
  lines.push("TOTAL " + money(total));
  return { ok: true, value: lines.join("; ") };
}
