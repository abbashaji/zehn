function streak_lengths(readings: number[]): number[] {
  const lengths: number[] = [];
  let prev: number | null = null;
  for (const x of readings) {
    const last = lengths.length - 1;
    if (prev !== null && x === prev) {
      lengths[last] = (lengths[last] ?? 0) + 1;
    } else {
      lengths.push(1);
    }
    prev = x;
  }
  return lengths;
}
