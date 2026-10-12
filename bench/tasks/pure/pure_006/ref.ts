type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function reduce_steps(n: number, cap: number): Result<number> {
  if (n < 1) {
    return { ok: false, error: "start must be positive" };
  }
  let size = n;
  let taken = 0;
  while (size !== 1) {
    if (taken >= cap) {
      return { ok: false, error: "step limit exceeded" };
    }
    size = size % 3 === 0 ? size / 3 : size + 1;
    taken++;
  }
  return { ok: true, value: taken };
}
