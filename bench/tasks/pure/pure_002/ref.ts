function next_tick(n: number, step: number): number {
  return n - (n % step) + step;
}
