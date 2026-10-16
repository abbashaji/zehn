function merge_unique(a: number[], b: number[]): number[] {
  const merged: number[] = [];
  let i = 0;
  let j = 0;
  while (i < a.length && j < b.length) {
    const x = a[i] ?? 0;
    const y = b[j] ?? 0;
    if (x < y) {
      merged.push(x);
      i++;
    } else if (x > y) {
      merged.push(y);
      j++;
    } else {
      merged.push(x);
      merged.push(y);
      i++;
      j++;
    }
  }
  while (j < b.length) {
    merged.push(b[j] ?? 0);
    j++;
  }
  return merged;
}
