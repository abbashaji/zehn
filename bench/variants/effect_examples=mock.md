## Dialect: mocked examples of effectful functions

In this dialect an `example` of a function that uses effects may carry a mock handler after the expression. The effects are then simulated; nothing touches the host.

```
example greet("Ada") with console = mock [] prints ["hello, Ada"]
example age(1900) == 126 with time.now = mock [2026]
```

- `with <effect> = mock [r1, r2]` lists, in order, the results of successive calls to that effect: `time.now` yields the listed Ints. `console.print` returns Unit, which has no literal, so write `with console = mock []`.
- `prints ["a", "b"]` asserts the exact texts passed to `console.print`, in order. It needs `with console = mock [...]`.
- Give one `with` clause for every effect that the called function declares in `uses`, and none for other effects (`E0605`). Running out of results is `E0606`; a result of the wrong type is `E0607`.
- An example with a mock clause may be a bare call of type Unit: it passes if it finishes and `prints` matches.
- Examples without a mock clause stay pure: calling an effectful function there is still `E0602`.
- Several `with` clauses are written in the order of the effect names (`console` before `time.now`), then `prints`.
