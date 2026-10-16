Target: SPEC.md section 8; action: add

### Explicit Int division (added by TASK_06c)

Three functions make the rounding of Int division visible in the name. All are `(Int, Int) -> Int`:

```
int.div_floor(a, b)     quotient rounded down toward negative infinity; same value as `a / b`
int.div_trunc(a, b)     quotient rounded toward zero (the fraction is dropped)
int.rem_euclid(a, b)    remainder r with 0 <= r < |b|; equals `a % b` only when b > 0
```

Examples: `int.div_floor(-7, 2) == -4`, `int.div_trunc(-7, 2) == -3`, `int.rem_euclid(-7, 2) == 1`,
`int.rem_euclid(7, -2) == 1` (while `7 % -2 == -1`). A zero divisor is `E0505`, blamed on the caller, exactly
like `/` and `%`. Fuel is the same as for the operators: the one step of the call expression, plus
`wa * wb` words when either operand is above 128 bits (`w = (bit_length >> 6) + 1`), charged before the work
and before the zero-divisor check. The floor remainder (`%` today) has no explicit name; there are no other
division functions.

The operators `/` and `%` keep their v0.3 meaning (floor semantics, ADR-0010) in the default dialect.

**Dialect `int_ops`** (`--dialect int_ops=operators|explicit`, default `operators`): under `explicit`
every `/` or `%` expression (in bodies, contracts and examples) is the error `E0312`; its `fix_hint` names the
three functions above. Under `operators` nothing changes. The flag exists to run an A/B experiment
(`bench/experiments/int_division/`); the decision between the options is ADR-0017 (status unmeasured).

New error code: `E0312` (operator `/` or `%` on Int under `int_ops=explicit`).
