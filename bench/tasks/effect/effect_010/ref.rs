fn print_pages(items: Vec<String>, size: i64) -> Result<i64, String> {
    if size < 1 {
        return Err(String::from("page size must be at least 1"));
    }
    if items.is_empty() {
        println!("(no items)");
        return Ok(0);
    }
    let len = items.len() as i64;
    let pages = (len + size - 1) / size;
    for (index, chunk) in items.chunks(size as usize).enumerate() {
        println!("-- page {} of {} --", index + 1, pages);
        for item in chunk {
            println!("{}", item);
        }
    }
    Ok(pages)
}
