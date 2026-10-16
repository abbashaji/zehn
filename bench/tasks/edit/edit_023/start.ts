type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function clean_tags(tags: string[], limit: number): Result<string[]> {
  const kept: string[] = [];
  for (const tag of tags) {
    if (!kept.includes(tag)) {
      kept.push(tag);
    }
  }
  return { ok: true, value: kept };
}
