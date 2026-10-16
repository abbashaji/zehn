function align_column(values: number[]): string {
  let width = 0;
  for (const v of values) {
    width = Math.max(width, String(v).length);
  }
  const cells: string[] = [];
  for (const v of values) {
    let cell = String(v);
    while (cell.length < width) {
      cell = " " + cell;
    }
    cells.push(cell);
  }
  return cells.join("|");
}
