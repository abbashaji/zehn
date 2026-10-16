function rotate_left(items: number[], k: number): number[] {
  if (items.length === 0) {
    return [];
  }
  const shift = k % items.length;
  return items.slice(shift).concat(items.slice(0, shift));
}
