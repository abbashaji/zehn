interface Item {
  name: string;
  price: number;
  stock: number;
}

function cheapest_in_stock(items: Item[]): string | null {
  let best: Item | null = null;
  for (const item of items) {
    if (item.stock >= 0 && (best === null || item.price <= best.price)) {
      best = item;
    }
  }
  return best === null ? null : best.name;
}
