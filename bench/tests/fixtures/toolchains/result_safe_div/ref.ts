type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function safe_div(a: number, b: number): Result<number> {
  if (b === 0) {
    return { ok: false, error: "division by zero" };
  }
  return { ok: true, value: Math.floor(a / b) };
}
