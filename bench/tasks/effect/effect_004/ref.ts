function problem(name: string): string | null {
  if (name.length < 3) {
    return "too short";
  }
  if (name.length > 12) {
    return "too long";
  }
  if (name.includes(" ")) {
    return "has space";
  }
  return null;
}

function validate_usernames(names: string[]): number {
  let failures = 0;
  for (const [i, name] of names.entries()) {
    const reason = problem(name);
    if (reason !== null) {
      console.log(`#${i + 1} [${name}]: ${reason}`);
      failures += 1;
    }
  }
  return failures;
}
