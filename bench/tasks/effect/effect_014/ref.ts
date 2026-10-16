interface Cmd {
  op: string;
  key: string;
  n: number;
}

function run_script(cmds: Cmd[]): number {
  const store = new Map<string, number>();
  for (const [i, cmd] of cmds.entries()) {
    const pos = i + 1;
    if (cmd.op === "set") {
      store.set(cmd.key, cmd.n);
    } else if (cmd.op === "add") {
      store.set(cmd.key, (store.get(cmd.key) ?? 0) + cmd.n);
    } else if (cmd.op === "get") {
      const value = store.get(cmd.key);
      if (value === undefined) {
        console.log(`${cmd.key}: unset`);
      } else {
        console.log(`${cmd.key} = ${value}`);
      }
    } else if (cmd.op === "del") {
      if (!store.delete(cmd.key)) {
        console.log(`nothing to delete: ${cmd.key}`);
      }
    } else if (cmd.op === "dump") {
      if (store.size === 0) {
        console.log("(empty)");
      } else {
        for (const [key, value] of store) {
          console.log(`${key}=${value}`);
        }
      }
    } else {
      console.log(`command ${pos}: bad op ${cmd.op}`);
    }
  }
  return store.size;
}
