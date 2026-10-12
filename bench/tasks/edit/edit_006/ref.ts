type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Booking {
  begin: number;
  finish: number;
}

function add_booking(bookings: Booking[], begin: number, finish: number, gap: number): Result<Booking[]> {
  if (begin >= finish) {
    return { ok: false, error: "invalid range" };
  }
  if (gap < 0) {
    return { ok: false, error: "invalid gap" };
  }
  for (const b of bookings) {
    if (begin < b.finish + gap && b.begin < finish + gap) {
      return { ok: false, error: "conflict" };
    }
  }
  const updated: Booking[] = [];
  let placed = false;
  for (const b of bookings) {
    if (!placed && b.begin > begin) {
      updated.push({ begin, finish });
      placed = true;
    }
    updated.push(b);
  }
  if (!placed) {
    updated.push({ begin, finish });
  }
  return { ok: true, value: updated };
}
