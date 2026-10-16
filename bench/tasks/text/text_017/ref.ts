type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function max_tag_depth(markup: string): Result<number> {
  const open: string[] = [];
  let deepest = 0;
  const pieces = markup.split("<");
  for (let i = 1; i < pieces.length; i++) {
    const tag = (pieces[i] ?? "").split(">")[0] ?? "";
    if (tag.startsWith("/")) {
      const name = tag.slice(1);
      const top = open[open.length - 1];
      if (top === undefined) {
        return { ok: false, error: "unexpected closing tag: " + name };
      }
      if (top !== name) {
        return { ok: false, error: "mismatched tag: expected " + top + ", found " + name };
      }
      open.pop();
    } else {
      open.push(tag);
      deepest = Math.max(deepest, open.length);
    }
  }
  const last = open[open.length - 1];
  if (last !== undefined) {
    return { ok: false, error: "unclosed tag: " + last };
  }
  return { ok: true, value: deepest };
}
