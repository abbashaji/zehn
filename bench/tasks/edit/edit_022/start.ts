function average_without_worst(scores: number[]): number | null {
  if (scores.length < 2) {
    return null;
  }
  const worst = Math.min(...scores);
  const rest = scores.filter((s) => s !== worst);
  if (rest.length === 0) {
    return null;
  }
  let total = 0;
  for (const s of rest) {
    total += s;
  }
  return Math.floor(total / rest.length);
}
