function print_numbered(items: string[]): number {
  for (const [i, item] of items.entries()) {
    console.log(`${i + 1}. ${item}`);
  }
  return items.length;
}
