fn matching_posts(posts: Vec<String>, tags: Vec<String>) -> Vec<String> {
    posts
        .into_iter()
        .filter(|p| tags.iter().any(|t| p.contains(t.as_str())))
        .collect()
}
