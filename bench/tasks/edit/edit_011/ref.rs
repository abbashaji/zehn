fn matching_posts(posts: Vec<String>, tags: Vec<String>) -> Vec<String> {
    let wanted: Vec<String> = tags.iter().map(|t| t.to_ascii_uppercase()).collect();
    posts
        .into_iter()
        .filter(|p| {
            let upper = p.to_ascii_uppercase();
            wanted.iter().all(|t| upper.contains(t.as_str()))
        })
        .collect()
}
