fn align_column(values: Vec<i64>) -> String {
    let cells: Vec<String> = values.iter().map(|v| v.to_string()).collect();
    let width = cells.iter().map(|c| c.len()).max().unwrap_or(0);
    let padded: Vec<String> = cells
        .iter()
        .map(|c| format!("{:>width$}", c, width = width))
        .collect();
    padded.join("|")
}
