fn csv_field_count(line: String) -> i64 {
    if line.is_empty() {
        return 0;
    }
    line.split(',').count() as i64
}
