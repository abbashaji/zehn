interface Seat {
  label: string;
  holder: string | null;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function book_seat(seats: Seat[], label: string, guest: string): Result<Seat[]> {
  if (guest === "") {
    return { ok: false, error: "guest name required" };
  }
  const target = seats.find((s) => s.label === label);
  if (target === undefined) {
    return { ok: false, error: "no such seat: " + label };
  }
  if (target.holder !== null) {
    return { ok: false, error: "seat already booked: " + label };
  }
  const held = seats.filter((s) => s.holder === guest).length;
  if (held >= 2) {
    return { ok: false, error: "booking limit reached for " + guest };
  }
  return { ok: true, value: seats.map((s) => (s.label === label ? { label: s.label, holder: guest } : s)) };
}
