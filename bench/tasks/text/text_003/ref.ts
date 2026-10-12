function count_word(sentence: string, word: string): number {
  let count = 0;
  for (const token of sentence.split(" ")) {
    if (token === word) {
      count += 1;
    }
  }
  return count;
}
