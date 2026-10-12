interface Line {
  name: string;
  qty: number;
  price: number;
}

function print_invoice(lines: Line[]): number {
  let total = 0;
  for (const line of lines) {
    const subtotal = line.qty * line.price;
    total += subtotal;
    console.log(`${line.name} x ${line.qty} @ ${line.price} = ${subtotal}`);
  }
  console.log(`TOTAL: ${total}`);
  return total;
}
