# Zehn (ذهن)

A language for LLMs as authors and humans as auditors. See `SPEC.md`.

```
python3 zehn.py check examples/transfer.zehn          # types, effects, return paths, contracts, examples
python3 zehn.py check errors/bad_types.zehn --json     # machine-readable diagnostics
python3 zehn.py fmt   examples/shapes.zehn --check     # canonical form
python3 zehn.py hash  examples/shapes.zehn             # fn#xxxx refs for patching
python3 zehn.py run   examples/effects.zehn greet '["Ali"]' --grant console
python3 zehn.py check errors/bad_termination.zehn      # unconditional recursion -> E0311, before any example runs
python3 zehn.py check errors/bad_termination_runtime.zehn  # guarded runaway recursion -> E0801 / E0802, never a hang
python3 zehn.py run   examples/recursion.zehn sum_to '[500]' --fuel 300 --max-depth 100
python3 zehn.py check dialects/int_ops=explicit/examples/explicit_div.zehn --dialect int_ops=explicit   # a dialect flag (repeatable)
python3 zehn.py --help                                  # the seven commands; check/run/fmt take --dialect name=value (repeatable)
python3 -m unittest discover -s tests                  # 337 tests
sh ci/run_ci.sh                                         # CI: compile, both test suites, fmt --check, offline light benchmark
```

Python 3.9+, no dependencies. `zehn.py` is a thin facade over the `zehnlib/` package (one module per
concern: lexer, parser, checker, typecheck, interp, cli, ...; the stdlib, the static passes and the commands are
registries filled by discovery, so a new one is a new file in `zehnlib/stdlib|passes|commands/`); `tests/golden/` pins the behaviour of every
program in `examples/` and `errors/`.
