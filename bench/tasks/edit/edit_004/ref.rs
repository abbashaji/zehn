struct Employee {
    name: String,
    dept: String,
    salary: i64,
    active: bool,
}

fn payroll_total(staff: Vec<Employee>, dept: Option<String>) -> i64 {
    let mut total = 0;
    for e in &staff {
        if !e.active {
            continue;
        }
        if let Some(d) = &dept {
            if !e.dept.eq_ignore_ascii_case(d) {
                continue;
            }
        }
        total += e.salary;
    }
    total
}
