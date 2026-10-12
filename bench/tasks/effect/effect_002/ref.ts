function log_long_words(words: string[], min_len: number): number {
  let count = 0;
  for (const word of words) {
    if (word.length >= min_len) {
      console.log(`LONG: ${word}`);
      count += 1;
    }
  }
  return count;
}
