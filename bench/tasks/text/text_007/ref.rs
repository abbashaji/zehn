fn longest_word(line: String) -> i64 {
    let mut best: i64 = 0;
    for word in line.split(' ') {
        best = best.max(word.len() as i64);
    }
    best
}
