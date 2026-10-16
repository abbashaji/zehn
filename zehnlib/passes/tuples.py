"""TASK_07: tuples. This module registers the explain texts of the tuple error codes; the checks
themselves live where the rest of the language lives (parser: E0316-E0318; type checker:
E0313-E0315; names pass: exhaustiveness of tuple patterns, E0301). It adds no static pass."""
from __future__ import annotations

from zehnlib.errors import explain

explain("E0313", "A tuple pattern has a different number of elements than the tuple it matches, "
                 "for example `case (x, y, z) =>` on a value of type (Int, Int). `expected` is "
                 "the type of the matched value. Write a pattern with exactly as many elements "
                 "as the tuple has; use `_` for the ones you do not need.")
explain("E0314", "A tuple has a different number of elements than the tuple type expected at "
                 "this place, for example `(1, 2, 3)` where a (Int, Int) is declared, or a "
                 "function that returns (Int, Int, Int) used as an (Int, Int). Tuple types have a "
                 "fixed size: `expected` and `found` give both types. Add or remove elements, or "
                 "change the declared type. A wrong element type inside a tuple of the right "
                 "size is E0306.")
explain("E0315", "A tuple pattern, such as `case (a, b) =>`, was used on a value that is not a "
                 "tuple. `expected` is the type of the matched value. Match it with a pattern of "
                 "its own type (a name, a literal, a constructor), or match the tuple that holds "
                 "it.")
explain("E0316", "`let` and `var` bind one name; there is no destructuring `let (a, b) = ...`. "
                 "Zehn has one way to take a tuple apart: bind the tuple to a name and use "
                 "`match t do case (a, b) => ... end match`.")
explain("E0317", "A tuple element cannot be read by position (`t.0`, `t.1`): tuples have no field "
                 "access. Take the tuple apart with `match t do case (a, b) => ... end match`, "
                 "or use a record type when the parts deserve names.")
explain("E0318", "A tuple has two or more elements. `()` and `(x,)` are not tuples, a type `(T)` "
                 "is not a one-element tuple type, and `(x)` is just `x` in parentheses. Write at "
                 "least two elements, or drop the parentheses.")
