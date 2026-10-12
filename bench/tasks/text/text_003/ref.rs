fn count_word(sentence: String, word: String) -> i64 {
    sentence.split(' ').filter(|t| *t == word).count() as i64
}
