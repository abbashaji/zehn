## Dialect: int_ops=explicit

In this dialect the operators `/` and `%` are not allowed on Int; using one is error `E0312`. Write Int division with these functions instead, each `(Int, Int) -> Int`:

- `int.div_floor(a, b)`: the quotient rounded down toward negative infinity (`int.div_floor(-7, 2)` is -4).
- `int.div_trunc(a, b)`: the quotient rounded toward zero (`int.div_trunc(-7, 2)` is -3).
- `int.rem_euclid(a, b)`: the remainder `r` with `0 <= r < |b|` (`int.rem_euclid(-7, 2)` is 1).

A zero divisor is still `E0505`, so keep `requires b != 0`. There is no function for a remainder that follows the sign of the dividend or of the divisor; compute it as `a - b * q` from the quotient you want. Pick the function that matches the rounding the task states.
