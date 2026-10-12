function lookup_value(config: string, key: string): string | null {
  for (const entry of config.split(";")) {
    const parts = entry.split("=");
    if (parts.length === 2 && parts[0] === key) {
      return parts[1] ?? null;
    }
  }
  return null;
}
