function longest_word(line: string): number {
  let best = 0;
  for (const word of line.split(" ")) {
    best = Math.max(best, word.length);
  }
  return best;
}
