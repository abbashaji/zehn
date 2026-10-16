use std::collections::HashMap;

fn longest_zero_sum(values: Vec<i64>) -> i64 {
    let mut firsts: HashMap<i64, i64> = HashMap::new();
    firsts.insert(0, 0);
    let mut total = 0;
    let mut best = 0;
    for (i, x) in values.iter().enumerate() {
        total += x;
        let len = i as i64 + 1;
        match firsts.get(&total) {
            Some(&first) => best = best.max(len - first),
            None => {
                firsts.insert(total, len);
            }
        }
    }
    best
}
