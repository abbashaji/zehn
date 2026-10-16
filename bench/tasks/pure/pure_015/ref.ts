function schedule_length(tasks: number[], cooldown: number): number {
  const last = new Map<number, number>();
  let now = 0;
  for (const kind of tasks) {
    now += 1;
    const prev = last.get(kind);
    if (prev !== undefined) {
      now = Math.max(now, prev + cooldown + 1);
    }
    last.set(kind, now);
  }
  return now;
}
