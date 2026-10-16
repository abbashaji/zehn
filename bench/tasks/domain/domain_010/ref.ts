type Result<T> = { ok: true; value: T } | { ok: false; error: string };

const STATUSES: string[] = ["new", "paid", "packed", "shipped", "delivered", "cancelled", "refunded"];
const EVENTS: string[] = ["pay", "pack", "ship", "deliver", "cancel", "refund"];

function nextStatus(status: string, event: string): string | null {
  if (status === "new" && event === "pay") {
    return "paid";
  }
  if (status === "paid" && event === "pack") {
    return "packed";
  }
  if (status === "packed" && event === "ship") {
    return "shipped";
  }
  if (status === "shipped" && event === "deliver") {
    return "delivered";
  }
  if (event === "cancel" && (status === "new" || status === "paid" || status === "packed")) {
    return "cancelled";
  }
  if (status === "delivered" && event === "refund") {
    return "refunded";
  }
  return null;
}

function apply_events(status: string, events: string[]): Result<string> {
  if (!STATUSES.includes(status)) {
    return { ok: false, error: "unknown status: " + status };
  }
  let current = status;
  let step = 0;
  for (const event of events) {
    step += 1;
    if (!EVENTS.includes(event)) {
      return { ok: false, error: "step " + step + ": unknown event " + event };
    }
    const following = nextStatus(current, event);
    if (following === null) {
      return { ok: false, error: "step " + step + ": cannot " + event + " when " + current };
    }
    current = following;
  }
  return { ok: true, value: current };
}
