function late_fee(days_late: number, daily: number, cap: number | null): number {
  if (days_late <= 3) {
    return 0;
  }
  return (days_late - 3) * daily;
}
