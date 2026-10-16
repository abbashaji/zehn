function scan_alerts(readings: number[], limit: number): number {
  let above = false;
  let started = 0;
  for (const [i, value] of readings.entries()) {
    const pos = i + 1;
    if (value > limit && !above) {
      console.log(`ALERT ${pos}: ${value}`);
      above = true;
      started += 1;
    } else if (value <= limit && above) {
      console.log(`CLEAR ${pos}: ${value}`);
      above = false;
    }
  }
  if (above) {
    console.log("still above at end");
  }
  return started;
}
