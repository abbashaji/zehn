use std::collections::HashMap;

fn schedule_length(tasks: Vec<i64>, cooldown: i64) -> i64 {
    let mut last: HashMap<i64, i64> = HashMap::new();
    let mut now = 0;
    for kind in tasks {
        now += 1;
        if let Some(&prev) = last.get(&kind) {
            now = now.max(prev + cooldown + 1);
        }
        last.insert(kind, now);
    }
    now
}
