fn scan_alerts(readings: Vec<i64>, limit: i64) -> i64 {
    let mut above = false;
    let mut started = 0;
    for (i, value) in readings.iter().enumerate() {
        let pos = i + 1;
        if *value > limit && !above {
            println!("ALERT {}: {}", pos, value);
            above = true;
            started += 1;
        } else if *value <= limit && above {
            println!("CLEAR {}: {}", pos, value);
            above = false;
        }
    }
    if above {
        println!("still above at end");
    }
    started
}
