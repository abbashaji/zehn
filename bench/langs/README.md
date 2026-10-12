# bench/langs: toolchains for the compiled comparison languages

Used by the adapters `ts_strict`, `rust` and `rust_strict` (`bench/benchlib/adapters/`).
Nothing here is a dependency of the project: the tools are run as programs, never imported or vendored.

## Install

```
npm install -g typescript                                   # tsc; node is needed too (22 here)
apt-get install -y rustc cargo rust-clippy rustfmt          # Ubuntu 24.04: Rust 1.75
# or, with rustup:  rustup component add clippy rustfmt
```

Each adapter's `available()` returns `(False, reason)` naming the missing programs
(`tsc`, `node` / `cargo`, `rustc`, plus `cargo-clippy`, `cargo-fmt`, `rustfmt` for `rust_strict`).

## Versions the adapters were verified with

| tool | version | where |
|---|---|---|
| node | 22.22.2 | sandbox |
| tsc | 6.0.3 (preinstalled) and 7.0.2 (`latest` on npm, installed into a temp prefix) | both pass the whole suite |
| rustc / cargo | 1.75.0 | `apt-get install rustc cargo` (Ubuntu 24.04) |
| clippy | 0.1.75 | `apt-get install rust-clippy` |
| rustfmt | 1.7.0-stable | `apt-get install rustfmt` |

Newer Rust releases have more clippy lints on by default and may format a few constructs differently,
so `rust_strict` verdicts can differ between toolchain versions: record the version with every benchmark run.

## Files

- `rust/Cargo.toml.tmpl`: crate manifest (edition 2021, no dependencies); written as `Cargo.toml` into the work directory (the `.tmpl` suffix keeps a `Cargo.toml` out of the repository tree).
- `rust/harness_prelude.rs.tmpl`: the JSON printer trait (`BenchJs`) for `i64 bool String () Vec<T> Option<T> Result<T, String>`; record impls are generated per task.
- `ts/tsconfig.json.tmpl`: `strict`, `noImplicitReturns`, `noUncheckedIndexedAccess`, `noFallthroughCasesInSwitch`, target ES2020, CommonJS, no `types`.
- `ts/bench_env.d.ts.tmpl`: ambient `console.log` (no `@types/node`, no `package.json`, no `node_modules`).

## How a program is built and tested

Work directory layout: `<workdir>/<adapter name>/`.

- **Rust**: `src/main.rs` = the model's text (byte for byte, first) + a generated `#[rustfmt::skip] mod bench_harness` + `fn main`. The harness is a child module, so it sees private items. `tool_check` builds a signature check (`let _sig: fn(..) -> .. = entry;`); `run_hidden` builds and runs a harness that calls `entry` for every test.
- **rust_strict** `tool_check`: `cargo build`; if that succeeds, `cargo clippy -- -D warnings` and `cargo fmt --check -- --color never` (both are run, so both kinds of diagnostic are reported). Formatting hunks become diagnostics with code `fmt` and the first changed line. `run_hidden` is the same as for `rust`: it measures behaviour, the strict verdict is the one from `tool_check`.
- **TypeScript**: `prog.ts` = the model's text + `export {};` + a generated harness; `tsc -p tsconfig.json --pretty false`, then `node out/prog.js`.
- Errors in the generated part (for example an `entry` whose signature differs from `task.json`) have `line: None`, a message starting with `(entry point check against the task signature)`, and `unknown_name: False`.
- Each test prints between marker characters `\x01B<i>\x02 ... \x01E<i>\x02<json>\x03`, so the program's own stdout (compared against the test's `stdout`, exactly) is kept apart from the result. The result is parsed and compared as compact JSON text in declared record field order. A build failure, a crash (non-zero exit, including a panic or an uncaught exception) and a timeout (10 s) all score `passed=0` with one failure entry that gives the reason.

## Unknown-name codes

`unknown_name` is true for TS2304, TS2339 and rustc E0425, E0433, E0412, E0599, only when the error is in the model's own code.
tsc reports the same conditions as TS2552 ("Cannot find name, did you mean ...") and TS2551 ("Property does not exist, did you mean ...") when a similar name exists; those are not in the list yet, so near-miss hallucinations are not counted for TypeScript.

## Value mapping per language (to be copied into bench/README.md at merge)

| Zehn | Python | TypeScript | Rust |
|---|---|---|---|
| Int | `int` | `number` (tests stay within +-2^53-1) | `i64` |
| Bool | `bool` | `boolean` | `bool` |
| Text | `str` (ASCII) | `string` | `String` |
| List<T> | `list` | `T[]` | `Vec<T>` |
| Option<T> | `Optional[T]` (`None` or the value) | `T \| null` | `Option<T>` |
| Result<T, Text> | `Ok(value)` / `Err(message)` from `bench_prelude.py` | `{ ok: true, value: T } \| { ok: false, error: string }` | `Result<T, String>` |
| record | `@dataclass` with the declared names | interface / object | struct with the declared names |
| console output | `print` | `console.log` | `println!` / `print!` |

All parameters are owned values in Rust. The model writes the record declarations itself in every language.
