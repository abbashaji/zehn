function first_even(xs: number[]): number | null {
  for (const x of xs) {
    if (x % 2 === 0) {
      return x;
    }
  }
  return null;
}
