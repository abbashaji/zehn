function next_state(state: string, event: string): string | null {
  if (state === "closed" && event === "open") {
    return "open";
  }
  if (state === "open" && event === "close") {
    return "closed";
  }
  if (state === "closed" && event === "lock") {
    return "locked";
  }
  if (state === "locked" && event === "unlock") {
    return "closed";
  }
  return null;
}

function run_door(events: string[]): string {
  let state = "closed";
  for (const event of events) {
    const moved = next_state(state, event);
    if (moved === null) {
      console.log(`ignored ${event} in ${state}`);
    } else {
      console.log(`${state} -> ${moved}`);
      state = moved;
    }
  }
  return state;
}
