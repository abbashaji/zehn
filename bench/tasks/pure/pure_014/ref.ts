type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function operands(op: string): number | null {
  switch (op) {
    case "push":
      return 0;
    case "dup":
    case "drop":
      return 1;
    case "swap":
    case "add":
    case "sub":
    case "mul":
      return 2;
    default:
      return null;
  }
}

function run_machine(ops: string[], args: number[]): Result<number> {
  if (ops.length !== args.length) {
    return { ok: false, error: "length mismatch" };
  }
  const stack: number[] = [];
  for (let i = 0; i < ops.length; i++) {
    const op = ops[i] ?? "";
    const arg = args[i] ?? 0;
    const need = operands(op);
    if (need === null) {
      return { ok: false, error: "unknown op at " + i };
    }
    if (stack.length < need) {
      return { ok: false, error: "stack underflow at " + i };
    }
    if (op === "push") {
      stack.push(arg);
    } else if (op === "dup") {
      stack.push(stack[stack.length - 1] ?? 0);
    } else if (op === "drop") {
      stack.pop();
    } else {
      const y = stack.pop() ?? 0;
      const x = stack.pop() ?? 0;
      if (op === "swap") {
        stack.push(y);
        stack.push(x);
      } else if (op === "add") {
        stack.push(x + y);
      } else if (op === "sub") {
        stack.push(x - y);
      } else {
        stack.push(x * y);
      }
    }
  }
  const top = stack[stack.length - 1];
  if (top === undefined) {
    return { ok: false, error: "empty stack" };
  }
  return { ok: true, value: top };
}
