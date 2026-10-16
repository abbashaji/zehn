function sign_changes(values: number[]): number {
  let changes = 0;
  let prev = 0;
  for (const x of values) {
    if (x === 0) {
      continue;
    }
    const sign = x > 0 ? 1 : -1;
    if (prev !== 0 && sign !== prev) {
      changes++;
    }
    prev = sign;
  }
  return changes;
}
