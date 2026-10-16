function trimmed_average(scores: number[], drop: number): number | null {
  if (scores.length === 0) {
    return null;
  }
  let total = 0;
  for (const s of scores) {
    total += s;
  }
  return Math.floor(total / scores.length);
}
