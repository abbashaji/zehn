# Task 02b (text_001..text_006): rejected tasks

Nothing was rejected: all six tasks are expressible in Zehn v0.3 as it is.

Workarounds that were needed (candidates for Phase 2 stdlib decisions, not rejections):
- No text indexing, trimming or text-to-Int parsing: the tasks avoid them by design (split on a separator, compare whole tokens).
- No loops: every scan is a recursive helper over `list.get(xs, i)` (all six tasks except text_001 need one).
- No `list.join` / `text.join`: text_002 (join with a separator) has to be written by hand with recursion.
- No `text.pad` / `int.to_text` width: text_006 pads cents with a small helper.
