type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Booking {
  begin: number;
  finish: number;
}

function add_booking(bookings: Booking[], begin: number, finish: number, gap: number): Result<Booking[]> {
  if (begin >= finish) {
    return { ok: false, error: "invalid range" };
  }
  for (const b of bookings) {
    if (begin < b.finish && b.begin < finish) {
      return { ok: false, error: "conflict" };
    }
  }
  return { ok: true, value: [...bookings, { begin, finish }] };
}
