function replace_all(source: string, pattern: string, replacement: string): string {
  if (pattern === "") {
    return source;
  }
  return source.split(pattern).join(replacement);
}
