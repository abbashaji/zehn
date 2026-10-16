type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function digit_count(n: number, base: number): Result<number> {
  if (n < 0) {
    return { ok: false, error: "negative number" };
  }
  if (base < 2) {
    return { ok: false, error: "base must be at least 2" };
  }
  let count = 1;
  let rest = n;
  while (rest >= base) {
    rest = Math.floor(rest / base);
    count++;
  }
  return { ok: true, value: count };
}
