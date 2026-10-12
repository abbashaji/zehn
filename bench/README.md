# Zehn bench

Benchmark core: task loader and validator, a model-in-the-loop runner with a repair loop, a results
store, model clients and language adapters. Stdlib only, Python 3.9+. Fully testable without an API key.

```
python3 bench/run.py list         [--tasks-dir D] [--only ids]
python3 bench/run.py verify-refs  --lang zehn,python_plain,python_strict [--tasks-dir D]
python3 bench/run.py run          --models stub:broken_then_fixed --lang zehn,python_plain --repeats 2 --run-id t1
python3 bench/run.py run          --models anthropic:<model-id> --lang zehn --dry-run     # counts only
python3 bench/run.py run          --models anthropic:<model-id> --lang zehn --yes         # costs money
python3 bench/run.py replay       --lang zehn,python_plain                                # stub:perfect, CI
python3 bench/run.py run          --models gemini:gemma-4-31b --lang zehn --yes           # free tier, scheduled
python3 bench/run.py status       --run-id R --models gemini:gemma-4-31b                  # done / remaining
python3 bench/run.py doctor       --lang zehn,python_plain,python_strict,ts_strict,rust,rust_strict
python3 -m unittest discover -s bench/tests
```

Options: `--lang` (repeatable or comma list, default `zehn`), `--tasks-dir` (repeatable, default
`bench/tasks`), `--only ids`, `--repeats N` (5), `--temperature F` (1.0), `--max-rounds N` (5 = first try
plus 4 repairs), `--variant k=v[,k=v]` (`default`), `--set-label dev|hidden` (`dev`), `--out DIR`
(`bench/results`), `--run-id ID`. A run directory that already holds records is overwritten only when
every model is a stub; a remote run needs `--force` for that, or `--resume` to continue it.

Run control: `--resume` (keep the run directory, skip every attempt whose key `(task_id, lang, variant,
model, repeat)` already has a record, append to the same `records.jsonl`; a last line cut short by a kill is
dropped and that run is redone), `--seed N` (1234), `--limit-margin F` (0.9), `--expected-output-tokens N`
(1500), `--max-output-tokens N` (8192, sent to `gemini:`/`openai:` models), `--rpm/--tpm/--rpd` (override
`bench/limits.json` per field), `--limits-file`, `--time-budget-minutes N` (stop starting new runs after N
minutes, finish the running ones, save, print `TIME_BUDGET_REACHED remaining=<n>`, exit 0). `--yes` is
required for every remote model. Exit codes: 0 also for `TIME_BUDGET_REACHED` and `QUOTA_EXHAUSTED
remaining=<n>` (every key out of quota; progress saved); 2 for a refusal that retrying cannot fix (bad
request, bad key, unknown model: `FATAL: ...`, nothing recorded for that run, fix and `--resume`).

Work order: repeat-major. Inside a repeat the tasks are interleaved round-robin over the categories (each
shuffled with the seed) and every task is followed by all its languages in a seeded order, so in any prefix
of the work list the languages differ by at most one run and, while every category has tasks left, the
categories differ by at most one task. `status` prints `done`, `remaining`, per-language counts, the number
of records that ended in an error and the estimated remaining calls.

Models: `stub:perfect` (the reference solution), `stub:broken_then_fixed` (a syntax error first, then the
reference), `stub:never_valid` (prose without code), `anthropic:<model-id>`. The Anthropic client reads
`ANTHROPIC_API_KEY` (the key is never written to a file or record), uses `max_tokens` 4096, retries HTTP 429
and 5xx with backoff, and reads token counts from the response `usage`. `ANTHROPIC_BASE_URL` redirects it
(used by the tests). **[UNVERIFIED]** the endpoint, headers (`x-api-key`, `anthropic-version`) and field
names were written from memory: check them against Anthropic's API documentation before a paid run.

`gemini:<model-id>` (also Gemma ids) reads `GEMINI_API_KEYS` (comma list; one key is a list of one);
`openai:<model-id>` reads `OPENAI_COMPAT_API_KEYS` and `OPENAI_COMPAT_BASE_URL` (`/chat/completions` is
appended). A remote run uses exactly one model spec, never fails over to another model, and its records keep
the full spec string in `model`. Keys appear in logs only as `key#1`, `key#2` and never in a file, record,
`meta.json` or commit; `meta.json` lists the model spec, the API host and the limits used. `GEMINI_BASE_URL`
redirects the Gemini client (used by the tests; leave it unset). The Gemini client calls
`POST https://generativelanguage.googleapis.com/v1beta/models/<id>:generateContent?key=<key>` with
`system_instruction`, `contents` (roles `user`/`model`), `generationConfig.temperature` and
`generationConfig.maxOutputTokens`; it counts `thoughtsTokenCount` as output tokens and drops reply parts
flagged `thought`. API version `v1beta`, read from Google's reference on 2026-10-12. Not confirmed on
Google's own pages (third-party documentation only): the finish reason `MAX_TOKENS` and the `thought` flag
(both are used to detect cut-off replies and reasoning text) and the layout of a 429 body; a 429 counts as
a daily quota when its text contains `quota_exceeded`, `per day` or `daily`. A reply cut off by the output
limit that holds no complete code block is an attempt with diagnostic `TRUNCATED`. If a Gemma model rejects
`system_instruction` the first call fails with `FATAL: ... HTTP 400` and the message says why; nothing is
recorded.

Rate limits (`bench/limits.json`, per key): a sliding 60 s window for requests and tokens per minute, a
persistent per-key counter per UTC date for requests per day (`<run dir>/quota_state.json`, counts only), all
kept inside `--limit-margin`. HTTP 429/503 (also 500/502/504 and network errors): `Retry-After` if present,
else exponential backoff with jitter, at most 6 tries; then the run ends with an `error` record. A 429 that
names a daily quota marks the key exhausted for this process and its run goes back to the queue. Google's day
resets at midnight Pacific while the counter follows the UTC date, so the margin is not a guarantee around
that hour; the 429 handling covers it. A run that ended with an `error` after retries is recorded, so
`--resume` does not redo it: check `status` (errored records) before trusting a finished run.

## Running the baseline for free

"No rate limits" does not exist on free tiers. The aim is to never hit them, never lose finished work and
finish unattended. The workflow `.github/workflows/baseline.yml` runs every 6 hours (and on demand) until the
run is complete and keeps its progress in the git branch `bench-data`.

Arithmetic (per model):
- runs = tasks x languages x models x repeats (30 x 6 x 1 x 5 = 900 for the full baseline)
- calls = runs x average rounds (one round is one call; assume about 2 until a pilot measures it: 1,800)
- days = calls / (rpd x keys)
- minutes = max(calls / rpm, tokens / tpm), with tokens = calls x average tokens per call. The Zehn prompt
  is about 5,000 tokens; the scheduler budgets `ceil(chars / 3.5) + 1500` per call, so with 16,000 tokens
  per minute only about two Zehn calls fit per minute. Rough estimate for Gemma 4 31B on one key (30 / 16K /
  14.4K): 1,800 calls x about 3,000 tokens = 5.4M tokens / (16K x 0.9) = about 6 hours; the request limits
  are not the bottleneck. These are estimates, not measurements.

Advice:
- Start with a pilot: `only` = 6 task ids, `repeats` = 1, then read `status` for the measured rounds.
- Which models are usable: a model with 20 requests per day is not (1,800 calls would take 90 days on one
  key). 500 per day (Flash Lite 3.1 / 3.5) needs about 4 days; 14,400 per day (Gemma 4) is limited by tokens
  per minute, not by the day.
- One run never mixes models: a different model is a different run with a different `--run-id`, compared by
  `report.py`. The workflow starts one job per model in `models`, run id `<run_id>-<model-slug>`.
- Keys: put them in the secret `GEMINI_API_KEYS` (comma separated). Google applies its limits per project,
  not per key, so extra keys from the same project add nothing. Using several accounts to multiply a free
  quota may be against the provider's terms; the design works with one key. For an OpenAI-compatible
  provider set the secret `OPENAI_COMPAT_API_KEYS` and the variable `OPENAI_COMPAT_BASE_URL`, and add the
  model's limits from your own account to `bench/limits.json` (the Groq entry there is a null placeholder).
- Limits in `bench/limits.json` for the Gemini models come from the builder's own account table: check them.

Steps:
1. Create a GitHub repository (a private one has a monthly minutes allowance; check it against the arithmetic).
2. Upload the project (the folder that holds `zehn.py`, `bench/` and `.github/`).
3. Settings > Secrets and variables > Actions: add the secret `GEMINI_API_KEYS`.
4. Add the repository variable `BASELINE_MODELS`, for example `gemini:gemma-4-31b`.
5. Actions > baseline > Run workflow: `only` = six ids, `repeats` = 1 (a pilot).
6. When it ends, download the artifact `baseline-results` (every run folder plus `REPORT.md`); then run the
   full baseline with the defaults and let the schedule continue it.

Notes: the first `doctor` step shows which Rust, Node and tool versions the runner really has (not checked
when this was written). GitHub may disable scheduled workflows after a period without repository activity
[UNVERIFIED, from memory]; dispatch the workflow again if that happens. The workflow has not been executed by
its author: review it line by line before the first run.

## Task layout

`bench/tasks/<category>/<task_id>/` with `task.json`, `tests.json`, `ref.zehn`, `ref.py`, `ref.ts`,
`ref.rs`, and for edit tasks `start.*`. Categories: `pure text domain effect edit`; `task_id` is
`<category>_<NNN>`. Folders whose name starts with `_` are skipped. A task root may also hold tasks directly
(`--tasks-dir bench/tasks/_demo`); a root whose own name starts with `_` is a fixture root and its ids do
not need the category prefix (that is how `demo_000` is a `pure` task). `task.json` and `tests.json` follow
the plan; `python3 bench/run.py list` validates every task it loads (types limited to `Int Bool Text
List<T> Option<T> Result<T, Text>` and declared records, at least 8 tests, JSON values checked against the
declared types, Int within signed 64-bit, Text ASCII, `stdout` only for console tasks).

Tests never divide or take a remainder with a negative operand, and use no floats, randomness or clock.

## Value mapping

| Zehn | Python | TypeScript | Rust |
|---|---|---|---|
| `Int` / `Bool` / `Text` | `int` / `bool` / `str` | `number` (safe-integer range) / `boolean` / `string` | `i64` / `bool` / `String` |
| `List<T>` | `list[T]` | `T[]` | `Vec<T>` |
| `Option<T>` | `Optional[T]` (`None` or the value) | `T \| null` | `Option<T>` |
| `Result<T, Text>` | `Ok(value)` / `Err(message)` from `bench_prelude.py`, annotated `Result[T]` | `{ ok: true, value: T } \| { ok: false, error: string }` | `Result<T, String>` |
| record | `@dataclass` with the declared names | interface / object | `struct`, all parameters owned |

The model writes the record declarations itself in every language. The Python adapters write
`bench_prelude.py` (Ok, Err, Result) next to the program. The TypeScript and Rust columns are the plan's
mapping; their adapters are not part of this core.

Tests encode values as JSON: Int/Bool/Text/List as JSON, `{"$":"some","args":[x]}`, `{"$":"none"}`,
`{"$":"ok","args":[x]}`, `{"$":"err","args":[x]}`, records as objects.

## Adapters

An adapter is a module in `bench/benchlib/adapters/` with an `Adapter` subclass that sets `name`
(auto-registered; see `base.py` for the contract). Here: `zehn` (`zehn.py check <file> --json --strict`
from the project root; hidden tests through `_zehn_runner.py`, which uses only `parse`, `Interp`,
`to_value`, `show`), `python_plain` (byte-compile, import, run the visible examples), `python_strict`
(plain plus `mypy --strict` and `ruff check --isolated --select E4,E7,E9,F`; the rule set is pinned so a
new ruff default cannot change results). Hidden tests run on the program as written, whatever the tool
said, so a program with a static error that still runs correctly counts as passing.

With `--variant k=v`, the Zehn adapter passes `--dialect k=v` to every zehn command (v0.3 has no such
flag; a later task adds it) and appends `bench/variants/k=v.md` to the system prompt if it exists.

**Add a language:** create `bench/benchlib/adapters/<name>.py` with a subclass of `Adapter` setting
`name` and `ext`, and implement `available`, `system_prompt`, `tool_check`, `run_hidden` (optional:
`external_tools = [...]` so their `--version` goes into `meta.json`). Add `ref<ext>` (and `start<ext>`
for edit tasks) to every task, then run `verify-refs --lang <name>`.

## Results

`bench/results/<run_id>/records.jsonl`, one JSON object per line, validated by `benchlib/schema.py`
before it is written:

```
{"schema":1,"run_id","set":"dev"|"hidden","task_id","category","kind","lang","variant","model","repeat",
 "temperature","rounds":[{"i","tool_ok","diag_codes":[str],"unknown_names":int,"in_tokens","out_tokens"}],
 "accepted_round":int|null,"first_try_pass":bool,"final_pass":bool,"final_tests":{"passed","total"},
 "total_in_tokens","total_out_tokens","wall_ms","error":str|null}
```

`first_try_pass` = attempt 1 passes every hidden test. The final program is the accepted one, or the last
attempt if none was accepted. `accepted_round` = first round whose `tool_ok` is true. A reply without a
fenced code block is an attempt with empty code and the diagnostic code `NOCODE`. `meta.json` holds the UTC
date, the CLI arguments, the sha256 of `zehn.py` and of every `.py` under `zehnlib/` (if present), the `--version` of
each external tool used, model ids and the Python version.

Metrics (computed elsewhere): pass@1 = mean `first_try_pass`; pass_repair = mean of (`accepted_round` not
null and `final_pass`); repair rounds = `accepted_round - 1` (never accepted: `max_rounds - 1`, reported as
censored); silent-bug rate = share of runs accepted but not `final_pass`; hallucination rate = sum of
`unknown_names` over sum of diagnostics; stability = mean over tasks of the variance of `first_try_pass`.

## Hidden set

**`bench/hidden_set/` must stay out of every project zip** (it is in `_ops/EXCLUDE.txt`; keep it there).
It is never read by default and this core never creates it. Point `--tasks-dir` at it explicitly and pass
`--set-label hidden`.
