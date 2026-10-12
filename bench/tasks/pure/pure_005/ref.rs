fn idle_time(starts: Vec<i64>, ends: Vec<i64>) -> Result<i64, String> {
    if starts.len() != ends.len() {
        return Err(String::from("length mismatch"));
    }
    let mut prev_start = starts.first().copied().unwrap_or(0);
    let mut cover_end = prev_start;
    let mut idle = 0;
    for (&s, &e) in starts.iter().zip(ends.iter()) {
        if e < s {
            return Err(String::from("bad interval"));
        }
        if s < prev_start {
            return Err(String::from("unsorted"));
        }
        if s > cover_end {
            idle += s - cover_end;
        }
        cover_end = cover_end.max(e);
        prev_start = s;
    }
    Ok(idle)
}
