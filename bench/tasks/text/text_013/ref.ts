type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Binding {
  key: string;
  value: string;
}

function lookup(bindings: Binding[], key: string): string | null {
  for (const b of bindings) {
    if (b.key === key) {
      return b.value;
    }
  }
  return null;
}

function fill_template(template: string, bindings: Binding[]): Result<string> {
  const parts = template.split("{");
  let out = parts[0] ?? "";
  for (let i = 1; i < parts.length; i++) {
    const halves = (parts[i] ?? "").split("}");
    if (halves.length !== 2) {
      return { ok: false, error: "unclosed placeholder" };
    }
    const key = halves[0] ?? "";
    const value = lookup(bindings, key);
    if (value === null) {
      return { ok: false, error: "unknown placeholder: " + key };
    }
    out += value + (halves[1] ?? "");
  }
  return { ok: true, value: out };
}
