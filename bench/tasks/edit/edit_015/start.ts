type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Shift {
  begin: number;
  finish: number;
}

function merge_shifts(shifts: Shift[], gap: number): Result<Shift[]> {
  if (shifts.some((s): boolean => s.begin >= s.finish)) {
    return { ok: false, error: "invalid shift" };
  }
  for (let i = 1; i < shifts.length; i++) {
    const prev = shifts[i - 1];
    const cur = shifts[i];
    if (prev !== undefined && cur !== undefined && cur.begin < prev.begin) {
      return { ok: false, error: "not sorted" };
    }
  }
  const merged: Shift[] = [];
  for (const s of shifts) {
    const last: Shift | undefined = merged[merged.length - 1];
    if (last !== undefined && s.begin < last.finish) {
      last.finish = Math.max(last.finish, s.finish);
    } else {
      merged.push({ begin: s.begin, finish: s.finish });
    }
  }
  return { ok: true, value: merged };
}
