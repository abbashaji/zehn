function matching_posts(posts: string[], tags: string[]): string[] {
  const result: string[] = [];
  for (const post of posts) {
    for (const tag of tags) {
      if (post.includes(tag)) {
        result.push(post);
        break;
      }
    }
  }
  return result;
}
