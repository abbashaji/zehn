fn second_largest(values: Vec<i64>) -> Option<i64> {
    let mut top: Option<i64> = None;
    let mut second: Option<i64> = None;
    for v in values {
        match top {
            Some(t) if v <= t => {
                if second < Some(v) {
                    second = Some(v);
                }
            }
            _ => {
                second = top;
                top = Some(v);
            }
        }
    }
    second
}
