Nothing rejected in 02a: all six pure tasks (pure_001 to pure_006) were expressible in Zehn v0.3 without missing features.

Notes for Phase 2 stdlib decisions (not rejections): there is no zip or index-free pairing of two lists, so pure_001 and pure_005 recurse with an index and carry an unreachable `err`/`0` branch for the second list; pure_004 avoids a sort by walking both lists.
