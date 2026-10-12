function add(a: number, b: number): number {
  switch (a) {
    case 1:
      b = b + 1;
    case 2:
      b = b + 2;
      break;
    default:
      break;
  }
  return a + b;
}
