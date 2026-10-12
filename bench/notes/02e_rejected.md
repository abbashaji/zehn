# 02e: rejected tasks

Nothing was rejected: all six edit tasks (edit_001 to edit_006) are expressible in Zehn v0.3 as it is.

## Friction seen while writing them (not rejections; input for the Phase 2 stdlib decisions)

- No closures and no extra arguments for `list.filter` / `list.map`: every filter that depends on a parameter (a department, an id) needs a hand-written index-recursion helper (`edit_004`, `edit_005`, `edit_006`).
- No list insert, take, slice or find: sorted insertion (`edit_006`) and "find by id" / "update by id" (`edit_005`) are done by index recursion with an accumulator.
- `end` is a keyword, so a record field cannot be called `end` (`edit_006` uses `begin` / `finish` in every language to stay comparable).
- `implies` binds tighter than `and`: `P implies A and B` parses as `(P implies A) and B`. Authors need parentheses; a first draft of two contracts here got this wrong.
