function matching_posts(posts: string[], tags: string[]): string[] {
  const wanted = tags.map((t): string => t.toUpperCase());
  return posts.filter((p): boolean => {
    const upper = p.toUpperCase();
    return wanted.every((t): boolean => upper.includes(t));
  });
}
