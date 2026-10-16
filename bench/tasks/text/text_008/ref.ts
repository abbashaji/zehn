function contains_all(content: string, keywords: string[]): boolean {
  const upper = content.toUpperCase();
  for (const keyword of keywords) {
    if (!upper.includes(keyword.toUpperCase())) {
      return false;
    }
  }
  return true;
}
