type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function run_ledger(opening: number, moves: number[]): Result<number> {
  if (opening < 0) {
    return { ok: false, error: "negative opening balance" };
  }
  let balance = opening;
  for (const [i, amount] of moves.entries()) {
    if (balance + amount < 0) {
      console.log(`move ${i + 1} rejected: ${amount}`);
    } else {
      balance += amount;
      console.log(`move ${i + 1} ok: balance ${balance}`);
    }
  }
  console.log(`final: ${balance}`);
  return { ok: true, value: balance };
}
