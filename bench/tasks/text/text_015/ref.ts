function word_counts(body: string): string {
  const counts = new Map<string, number>();
  for (const word of body.split(" ")) {
    if (word === "") {
      continue;
    }
    const key = word.toUpperCase();
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const pieces: string[] = [];
  for (const [key, n] of counts) {
    pieces.push(key + "=" + String(n));
  }
  return pieces.join(", ");
}
