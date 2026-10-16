type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function check_requests(times: number[], window: number, limit: number): Result<number> {
  if (window < 1) {
    return { ok: false, error: "window must be positive" };
  }
  if (limit < 0) {
    return { ok: false, error: "limit must not be negative" };
  }
  let current = -1;
  let count = 0;
  let blocked = 0;
  for (const t of times) {
    const index = Math.floor(t / window);
    if (index !== current) {
      current = index;
      count = 0;
    }
    if (count < limit) {
      count += 1;
      console.log(`t=${t} allowed (${count}/${limit})`);
    } else {
      console.log(`t=${t} blocked`);
      blocked += 1;
    }
  }
  console.log(`blocked: ${blocked}`);
  return { ok: true, value: blocked };
}
