# Task 02c (domain, domain_001 to domain_006): rejected tasks

Nothing was rejected: all six tasks are expressible in Zehn v0.3 as it is.

Friction seen while writing the Zehn references (input for the Phase 2 stdlib decisions, not a rejection):

- No loops and no list search or update: every "find the record with this key" and "copy the list with one record changed" needs its own recursive helper over an index (`list.get(xs, i)` plus `list.concat`). Four of the six tasks carry two or three such helpers. A `list.find` / `list.update`-style function would remove most of them.
- Error messages with several parts need nested two-argument `text.concat` calls (up to five levels in domain_002 and domain_006). A `text.join` over a list, or a variadic concat, would shorten them.
- `Option<Text>` as a record field (domain_003) works in Zehn and in all three comparison languages.
