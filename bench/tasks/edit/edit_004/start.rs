struct Employee {
    name: String,
    dept: String,
    salary: i64,
    active: bool,
}

fn payroll_total(staff: Vec<Employee>, _dept: Option<String>) -> i64 {
    let mut total = 0;
    for e in &staff {
        if e.active {
            total += e.salary;
        }
    }
    total
}
