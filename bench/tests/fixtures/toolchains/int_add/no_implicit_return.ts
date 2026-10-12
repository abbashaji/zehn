function helper(x: number): number | undefined {
  if (x > 0) {
    return x;
  }
}

function add(a: number, b: number): number {
  return a + b + (helper(1) ?? 0);
}
