type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function max_depth(steps: number[]): Result<number> {
  let depth = 0;
  let deepest = 0;
  for (const s of steps) {
    if (s === 1) {
      depth++;
      deepest = Math.max(deepest, depth);
    } else if (s === -1) {
      if (depth === 0) {
        return { ok: false, error: "closed too early" };
      }
      depth--;
    } else {
      return { ok: false, error: "bad step" };
    }
  }
  if (depth > 0) {
    return { ok: false, error: "left open" };
  }
  return { ok: true, value: deepest };
}
