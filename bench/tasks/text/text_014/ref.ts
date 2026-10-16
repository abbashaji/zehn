type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function wrap_words(body: string, width: number): Result<string> {
  if (width < 1) {
    return { ok: false, error: "width must be positive" };
  }
  const lines: string[] = [];
  let line = "";
  for (const word of body.split(" ")) {
    if (word === "") {
      continue;
    }
    if (line === "") {
      line = word;
    } else if (line.length + 1 + word.length <= width) {
      line = line + " " + word;
    } else {
      lines.push(line);
      line = word;
    }
  }
  if (line !== "") {
    lines.push(line);
  }
  return { ok: true, value: lines.join("|") };
}
