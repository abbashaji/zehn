type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function normalize_headers(line: string): Result<string> {
  const seen: string[] = [];
  const parts = line.split(",");
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i] ?? "";
    if (part === "") {
      return { ok: false, error: "empty header at position " + String(i + 1) };
    }
    const upper = part.toUpperCase();
    if (seen.includes(upper)) {
      return { ok: false, error: "duplicate header: " + upper };
    }
    seen.push(upper);
  }
  return { ok: true, value: seen.join(",") };
}
