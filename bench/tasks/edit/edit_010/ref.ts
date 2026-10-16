function trimmed_average(scores: number[], drop: number): number | null {
  if (scores.length === 0) {
    return null;
  }
  const k = Math.min(Math.max(drop, 0), scores.length - 1);
  const kept = [...scores].sort((a, b) => a - b).slice(k);
  let total = 0;
  for (const s of kept) {
    total += s;
  }
  return Math.floor(total / kept.length);
}
