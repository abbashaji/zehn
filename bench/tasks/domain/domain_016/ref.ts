type Result<T> = { ok: true; value: T } | { ok: false; error: string };

const PRICES: { [plan: string]: number } = { free: 0, basic: 900, pro: 2900, team: 7900 };

function priceOf(plan: string): number | null {
  const price = PRICES[plan];
  if (price === undefined || !Object.prototype.hasOwnProperty.call(PRICES, plan)) {
    return null;
  }
  return price;
}

function change_plan(current: string, target: string, days_used: number, cycle_days: number): Result<number> {
  const fromPrice = priceOf(current);
  if (fromPrice === null) {
    return { ok: false, error: "unknown plan: " + current };
  }
  const toPrice = priceOf(target);
  if (toPrice === null) {
    return { ok: false, error: "unknown plan: " + target };
  }
  if (cycle_days <= 0 || days_used < 0 || days_used > cycle_days) {
    return { ok: false, error: "invalid cycle" };
  }
  if (current === target) {
    return { ok: false, error: "already on plan " + current };
  }
  if (target === "team" && current !== "pro") {
    return { ok: false, error: "team plan requires pro" };
  }
  if (toPrice < fromPrice && days_used > 7) {
    return { ok: false, error: "downgrade not allowed after day 7" };
  }
  const daysLeft = cycle_days - days_used;
  const charge = Math.floor((toPrice * daysLeft) / cycle_days);
  const credit = Math.floor((fromPrice * daysLeft) / cycle_days);
  return { ok: true, value: charge - credit };
}
