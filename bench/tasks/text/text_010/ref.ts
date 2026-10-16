type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function with_commas(n: number): Result<string> {
  if (n < 0) {
    return { ok: false, error: "negative number: " + String(n) };
  }
  let digits = String(n);
  const groups: string[] = [];
  while (digits.length > 3) {
    groups.unshift(digits.slice(-3));
    digits = digits.slice(0, digits.length - 3);
  }
  groups.unshift(digits);
  return { ok: true, value: groups.join(",") };
}
