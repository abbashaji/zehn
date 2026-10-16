type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function retry_log(outcomes: boolean[], max_attempts: number, base: number): Result<number> {
  if (max_attempts < 1) {
    return { ok: false, error: "no attempts allowed" };
  }
  let wait = Math.min(base, 60);
  for (let attempt = 1; attempt <= max_attempts; attempt++) {
    if (attempt <= outcomes.length && outcomes[attempt - 1]) {
      console.log(`attempt ${attempt}: ok`);
      return { ok: true, value: attempt };
    }
    console.log(`attempt ${attempt}: failed`);
    if (attempt < max_attempts) {
      console.log(`waiting ${wait}`);
      wait = Math.min(wait * 2, 60);
    }
  }
  return { ok: false, error: `gave up after ${max_attempts} attempts` };
}
