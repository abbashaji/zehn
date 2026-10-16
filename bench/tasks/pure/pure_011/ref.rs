struct Span {
    lo: i64,
    hi: i64,
}

fn merge_spans(spans: Vec<Span>) -> Vec<Span> {
    let mut merged: Vec<Span> = Vec::new();
    for s in spans {
        match merged.last_mut() {
            Some(last) if s.lo <= last.hi => last.hi = last.hi.max(s.hi),
            _ => merged.push(s),
        }
    }
    merged
}
