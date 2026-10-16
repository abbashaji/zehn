type Result<T> = { ok: true; value: T } | { ok: false; error: string };

const FREE_MINUTES = 15;
const BLOCK_MINUTES = 1440;
const HOUR_RATE = 300;
const BLOCK_CAP = 1500;

function parking_fee(entry: number, exit: number): Result<number> {
  if (entry < 0) {
    return { ok: false, error: "invalid entry time" };
  }
  if (exit < entry) {
    return { ok: false, error: "exit before entry" };
  }
  let remaining = exit - entry;
  let grace = FREE_MINUTES;
  let fee = 0;
  while (remaining > 0) {
    const block = Math.min(remaining, BLOCK_MINUTES);
    const billable = Math.max(0, block - grace);
    fee += Math.min(BLOCK_CAP, Math.floor((billable + 59) / 60) * HOUR_RATE);
    grace = 0;
    remaining -= block;
  }
  return { ok: true, value: fee };
}
