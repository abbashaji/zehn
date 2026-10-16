function average_without_worst(scores: number[]): number | null {
  if (scores.length < 3) {
    return null;
  }
  const worst = Math.min(...scores);
  const rest = [...scores];
  rest.splice(rest.indexOf(worst), 1);
  let total = 0;
  for (const s of rest) {
    total += s;
  }
  return Math.floor((2 * total + rest.length) / (2 * rest.length));
}
