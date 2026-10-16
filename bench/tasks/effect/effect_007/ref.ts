function countdown(start: number, step: number): number {
  if (step <= 0) {
    console.log(`bad step: ${step}`);
    return 0;
  }
  let printed = 0;
  let value = start;
  while (value > 0) {
    console.log(`T-minus ${value}`);
    printed += 1;
    value -= step;
  }
  console.log("liftoff");
  return printed;
}
