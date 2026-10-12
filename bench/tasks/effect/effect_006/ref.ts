interface Cmd {
  op: string;
  n: number;
}

function run_commands(cmds: Cmd[]): number {
  let acc = 0;
  for (const [i, cmd] of cmds.entries()) {
    const pos = i + 1;
    if (cmd.op === "add") {
      acc += cmd.n;
    } else if (cmd.op === "sub") {
      acc -= cmd.n;
    } else if (cmd.op === "mul") {
      acc *= cmd.n;
    } else if (cmd.op === "show") {
      console.log(`acc = ${acc}`);
    } else if (cmd.op === "halt") {
      console.log(`halted at command ${pos}`);
      break;
    } else {
      console.log(`command ${pos}: unknown op [${cmd.op}]`);
    }
  }
  return acc;
}
