# Task 04c (text_007..text_017): rejected tasks

Nothing was rejected: all eleven tasks are expressible in Zehn v0.3 as it is (11 of 11 kept).

Calibration (bench/BASELINE_v0.3.md, "Calibration for growth"): category `text` is at the pass@1 ceiling for
python_plain, python_strict, rust and rust_strict (1.000), with no floors in the category. As that section advises,
the levels were shifted harder than 30/40/30: 2 at level 1, 4 at level 2, 5 at level 3 (about 18/36/45%). The
level-3 tasks add an ordered error rule or a stack/invariant (text_013, 014, 016, 017) or a first-appearance
order with case folding (text_015). The baseline was one model; no pass_repair figure for the new tasks exists yet.

Ideas considered and dropped before writing (not expressible in Zehn v0.3 without a workaround that would change
the task; candidates for the Phase 2 stdlib decisions):
- Compare two dotted version strings ("1.10.2" vs "1.9"): needs text-to-Int parsing; Zehn has no way to read a number from a text.
- Palindrome check, run-length encoding of characters, acronym/initials, title case, caesar shift: need character indexing, substrings or `text.to_lower`; none exists.
- Sort words alphabetically: `<` is only defined on Int (E0306 on Text), so Text has no ordering.

Workarounds that were needed (friction, not rejections):
- No `text.join`: text_009, 011, 012, 014, 015, 016 write the join by hand with a recursive helper (same friction as text_002).
- No character access: text_017 detects a closing tag by splitting the tag on "/" and testing for two pieces; text_013 finds the end of a placeholder by splitting on "}".
- No list slicing or `list.pop`: text_016 and text_017 pop a stack by rebuilding the list (`pop` helper). Two refs now carry the same helper.
- No loops: every scan is a recursive helper over `list.get(xs, i)` (text_007 uses `list.fold` with a named function).
- `text` is a reserved namespace in Zehn, so no task parameter can be called `text`; the new tasks use `line`, `content`, `source`, `body`, `template`, `path`, `markup`.
- text_015 uses `Map<Text, Int>` inside helper signatures of the Zehn reference only; the task signature is `Text -> Text`, so the category rule holds. Reference ts/rs/py use a Map, a Vec of pairs and a dict.
- text_011 relies on "\n" inside Zehn string literals (works in v0.3).
