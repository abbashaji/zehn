# Zehn (ذهن)

A language for LLMs as authors and humans as auditors. See `SPEC.md`.

```
python3 zehn.py check examples/transfer.zehn          # types, effects, return paths, contracts, examples
python3 zehn.py check errors/bad_types.zehn --json     # machine-readable diagnostics
python3 zehn.py fmt   examples/shapes.zehn --check     # canonical form
python3 zehn.py hash  examples/shapes.zehn             # fn#xxxx refs for patching
python3 zehn.py run   examples/effects.zehn greet '["Ali"]' --grant console
python3 zehn.py check errors/bad_termination.zehn      # runaway recursion -> E0801 / E0802, never a hang
python3 zehn.py run   examples/recursion.zehn sum_to '[500]' --fuel 300 --max-depth 100
python3 -m unittest discover -s tests                  # 78 tests
```

Single file, Python 3.9+, no dependencies.
