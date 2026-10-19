"""Texts for `zehn explain` (EXPLAIN) and the fix hints attached to runtime diagnostics (HINTS).

Moved unchanged out of errors.py; registered through errors.explain / errors.hint."""
from __future__ import annotations

from zehnlib.errors import explain, hint


hint("E0401", "the body or the example is wrong; left is the computed value, right is the expected value")
hint("E0501", "check the precondition before calling, or make the function return err")
hint("E0502", "fix the implementation or weaken the ensures clause")
hint("E0801", "most likely non-terminating recursion: check that every recursive call moves toward a base case")
hint("E0802", "most likely unbounded recursion: add or fix the base case; Zehn has no tail-call optimization")


explain("E0001", "Bad command line: a non-numeric --fuel, --max-depth or --now, or a --dialect that is not name=value or names an unknown flag or value. The message names the option. Fix it and run again (`zehn.py --help` shows the usage); the exit code is 2.")
explain("E0101", "Lexing error: the source contains a character that is not part of the language (for example `@`, `$` or `'`). Remove it; text goes in double quotes and comments start with `--`.")
explain("E0201", "Parse error: the token found is not what the grammar allows here, for example a missing operand, `do` or `end <kind>`. The message names the expected and the found token; fix the source at that line (SPEC section 2 has the grammar).")
explain("E0202", "Two top-level definitions (functions, types or constructors) have the same name. Rename one of them or delete the duplicate.")
explain("E0301", "A match does not cover every case. Add the missing cases or a `case _ =>` branch.")
explain("E0302", "A name, constructor, or stdlib function does not exist. The fix_hint lists close matches.")
explain("E0303", "Wrong number of arguments for a function, constructor or pattern. Compare the call with the signature and pass exactly one argument per parameter.")
explain("E0304", "`?` was used in a function whose return type is not Result or Option, so there is nowhere to return the failure. Change the return type to Result<...> or Option<...>, or handle the value with `match`.")
explain("E0305", "Assignment `:=` to a name that was not declared with `var` (a `let` or a parameter). Declare it with `var` if it must change, or bind a new name with `let`.")
explain("E0203", "Strict mode: the source is not in canonical form. Run `zehn fmt <file> --write`.")
explain("E0204", "The source is nested too deeply for the parser (expressions or blocks inside each other). Split it into smaller functions.")
explain("E0310", "Some path through the function body reaches the end without `return`. `falls_through` lists every such path. Add a `return` there, or restructure so every `if` has an `else` that returns.")
explain("E0306", "Type mismatch found by the static type checker. `expected` and `found` give both types; fix_hint suggests a conversion when one exists.")
explain("E0308", "A record literal or field access does not fit any declared record type (unknown or duplicate field, wrong field set, or not a record). Check the names against the `type` declaration.")
explain("E0309", "The type cannot be inferred at this point. Add a type annotation, e.g. `let x: Account = ...`.")
explain("E0307", "A name is already defined in scope (shadowing is not allowed) or is reserved (such as `out` or a stdlib namespace like `list`). Choose a different name.")
explain("E0401", "An example evaluated to something other than true. `values` shows the left side (actual) and the right side (expected). Fix the body if the actual value is wrong, or the example if the expectation is.")
explain("E0402", "Strict mode: a pure function has no example. Add at least one, written `example f(x) == expected`. A function that declares effects (`uses [...]`) is exempt: an example may not call it (E0602).")
explain("E0501", "A precondition (requires) failed at run time. The caller is to blame: check the precondition before calling, or let the function return err instead of requiring it.")
explain("E0502", "A postcondition (ensures) failed at run time. The implementation is to blame: fix the body, or weaken the ensures clause if it was wrong.")
explain("E0503", "Internal guard: the body ended without `return` at run time. E0310 rejects this statically, so seeing E0503 means the static check was bypassed.")
explain("E0504", "Field access on a value that is not a record, or on a record without that field. E0308 normally prevents this statically; it appears when `zehn run` gets JSON arguments of the wrong shape. Pass a record with the declared fields.")
explain("E0505", "Division or modulo by zero. Guard with `requires b != 0`.")
explain("E0506", "No case of a match matched at run time. E0301 rejects non-exhaustive matches statically, so this appears when `zehn run` gets a JSON variant the type does not declare. Pass a declared constructor.")
explain("E0507", "result.unwrap was applied to an err value. Match on the result (`case ok(v)` and `case err(e)`) or test it with result.is_ok first.")
explain("E0601", "A function calls another function, or an effectful stdlib function, whose effects it did not declare in `uses`. Add the effect to the caller's `uses [...]`, or stop calling it.")
explain("E0602", "Contracts and examples must be pure: they cannot call functions or stdlib functions that have effects. Move the effectful call into a function body and test the pure part.")
explain("E0603", "An effectful stdlib function ran inside a function that did not declare the effect in `uses`. E0601 rejects this statically, so seeing E0603 means the static check was bypassed. Add the effect to `uses`.")
explain("E0604", "The host did not grant a capability the program declared. Pass --grant <effect> to `zehn run`.")
explain("E0701", "Patch: no definition has that content hash (it changed, or the ref is wrong). Run `zehn hash` for current refs.")
explain("E0702", "Patch: the hash prefix matches several definitions. Use a longer prefix.")
explain("E0703", "Patch: the replacement is not exactly one definition of the same kind, or --with is missing. Give --with a file that holds exactly one definition of the kind being replaced.")
explain("E0801", "The fuel budget ran out. One step is one expression or statement evaluated, plus a size charge for operations that touch whole lists, texts, maps or big integers. The usual cause is recursion that never reaches its base case; `call_stack` shows where. If the work is genuinely large, raise `--fuel`.")
explain("E0802", "The call depth limit was exceeded (default 10000 nested calls). `call_stack` shows the repeating frames. Zehn has no tail-call optimization, so deep recursion over big inputs should use list.fold / list.map instead, or raise `--max-depth`.")
explain("W0101", "A pure function has no example. Add at least one. A function that declares effects (`uses [...]`) is exempt: an example may not call it (E0602).")
explain("W0102", "A statement follows a `return` (or an if/match whose every branch returns), so it can never run. Delete it.")
explain("W0201", "Intent drift: body, contracts or examples changed but the intent text did not. Re-read the intent, then run `zehn lock <file>` to confirm.")
explain("W0301", "The source is not in canonical form (see `zehn fmt`). An error under --strict (E0203).")
