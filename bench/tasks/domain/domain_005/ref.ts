interface Member {
  name: string;
  points: number;
  tier: string;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

const POINT_CAP = 10000;

function multiplier(tier: string): number | null {
  if (tier === "bronze") {
    return 1;
  }
  if (tier === "silver") {
    return 2;
  }
  if (tier === "gold") {
    return 3;
  }
  return null;
}

function tier_for(points: number): string {
  if (points < 1000) {
    return "bronze";
  }
  if (points < 5000) {
    return "silver";
  }
  return "gold";
}

function apply_purchases(m: Member, spends: number[]): Result<Member> {
  if (m.points < 0 || m.points > POINT_CAP) {
    return { ok: false, error: "invalid member: points out of range" };
  }
  if (multiplier(m.tier) === null) {
    return { ok: false, error: "unknown tier: " + m.tier };
  }
  let current: Member = { name: m.name, points: m.points, tier: m.tier };
  let position = 0;
  for (const spend of spends) {
    position += 1;
    if (spend < 0) {
      return { ok: false, error: "purchase " + position + ": negative spend" };
    }
    const factor = multiplier(current.tier) ?? 1;
    const total = Math.min(POINT_CAP, current.points + Math.floor(spend / 10) * factor);
    current = { name: current.name, points: total, tier: tier_for(total) };
  }
  return { ok: true, value: current };
}
