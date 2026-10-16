function number_lines(body: string): string {
  const out: string[] = [];
  let n = 0;
  for (const line of body.split("\n")) {
    if (line === "") {
      out.push("");
    } else {
      n += 1;
      out.push(String(n) + ". " + line);
    }
  }
  return out.join("\n");
}
