struct Job {
    id: i64,
    burst: i64,
}

fn finish_order(jobs: Vec<Job>, quantum: i64) -> Result<Vec<i64>, String> {
    if quantum <= 0 {
        return Err("invalid quantum".to_string());
    }
    if jobs.iter().any(|j| j.burst <= 0) {
        return Err("invalid burst".to_string());
    }
    let mut queue = jobs;
    let mut done = Vec::new();
    while !queue.is_empty() {
        let job = queue.remove(0);
        if job.burst <= quantum {
            done.push(job.id);
        } else {
            queue.push(Job {
                id: job.id,
                burst: job.burst - quantum,
            });
        }
    }
    Ok(done)
}
