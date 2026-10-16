type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function clean_tags(tags: string[], limit: number): Result<string[]> {
  if (limit < 1) {
    return { ok: false, error: "invalid limit" };
  }
  const cleaned: string[] = [];
  const seen: string[] = [];
  for (const tag of tags) {
    const key = tag.toUpperCase();
    if (tag === "" || seen.includes(key)) {
      continue;
    }
    cleaned.push(tag);
    seen.push(key);
  }
  if (cleaned.length > limit) {
    return { ok: false, error: "too many tags" };
  }
  return { ok: true, value: cleaned };
}
