fn log_long_words(words: Vec<String>, min_len: i64) -> i64 {
    let mut count = 0;
    for word in &words {
        let len = word.len() as i64;
        if len >= min_len {
            println!("LONG: {}", word);
            count += 1;
        }
    }
    count
}
