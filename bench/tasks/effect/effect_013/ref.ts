interface Row {
  name: string;
  qty: number;
}

function print_table(rows: Row[]): number {
  let nameW = 4;
  let qtyW = 3;
  for (const row of rows) {
    nameW = Math.max(nameW, row.name.length);
    qtyW = Math.max(qtyW, String(row.qty).length);
  }
  console.log(`${"item".padEnd(nameW)} | ${"qty".padStart(qtyW)}`);
  console.log(`${"-".repeat(nameW)}-+-${"-".repeat(qtyW)}`);
  for (const row of rows) {
    console.log(`${row.name.padEnd(nameW)} | ${String(row.qty).padStart(qtyW)}`);
  }
  return nameW + 3 + qtyW;
}
