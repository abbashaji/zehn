interface Cmd {
  op: string;
  n: number;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function run_stack(cmds: Cmd[]): Result<number> {
  const stack: number[] = [];
  for (const [i, cmd] of cmds.entries()) {
    const pos = i + 1;
    if (cmd.op === "push") {
      stack.push(cmd.n);
    } else if (cmd.op === "pop" || cmd.op === "dup" || cmd.op === "add" || cmd.op === "mul" || cmd.op === "swap") {
      const needed = cmd.op === "pop" || cmd.op === "dup" ? 1 : 2;
      if (stack.length < needed) {
        return { ok: false, error: `stack underflow at command ${pos}` };
      }
      if (cmd.op === "pop") {
        stack.pop();
      } else if (cmd.op === "dup") {
        stack.push(stack[stack.length - 1] ?? 0);
      } else {
        const top = stack.pop() ?? 0;
        const below = stack.pop() ?? 0;
        if (cmd.op === "add") {
          stack.push(below + top);
        } else if (cmd.op === "mul") {
          stack.push(below * top);
        } else {
          stack.push(top);
          stack.push(below);
        }
      }
    } else {
      return { ok: false, error: `unknown op at command ${pos}` };
    }
    console.log(`${pos}: [${stack.join(",")}]`);
  }
  const last = stack[stack.length - 1];
  if (last === undefined) {
    return { ok: false, error: "empty stack at end" };
  }
  return { ok: true, value: last };
}
