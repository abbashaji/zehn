function late_fee(days_late: number, daily: number, cap: number | null): number {
  const fee = days_late <= 3 ? 0 : (days_late - 3) * daily;
  if (cap === null) {
    return fee;
  }
  return Math.min(fee, Math.max(cap, 0));
}
