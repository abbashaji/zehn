function print_head(items: string[], limit: number): number {
  const shown = Math.max(0, Math.min(limit, items.length));
  for (const item of items.slice(0, shown)) {
    console.log(`- ${item}`);
  }
  if (items.length > shown) {
    console.log(`... and ${items.length - shown} more`);
  }
  return shown;
}
