type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function normalize_path(path: string): Result<string> {
  const stack: string[] = [];
  for (const segment of path.split("/")) {
    if (segment === "" || segment === ".") {
      continue;
    }
    if (segment === "..") {
      if (stack.length === 0) {
        return { ok: false, error: "path escapes root" };
      }
      stack.pop();
    } else {
      stack.push(segment);
    }
  }
  return { ok: true, value: "/" + stack.join("/") };
}
