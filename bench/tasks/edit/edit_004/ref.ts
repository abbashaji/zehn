interface Employee {
  name: string;
  dept: string;
  salary: number;
  active: boolean;
}

function payroll_total(staff: Employee[], dept: string | null): number {
  let total = 0;
  for (const e of staff) {
    if (!e.active) {
      continue;
    }
    if (dept !== null && e.dept.toUpperCase() !== dept.toUpperCase()) {
      continue;
    }
    total += e.salary;
  }
  return total;
}
