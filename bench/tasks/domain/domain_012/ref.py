from __future__ import annotations

from typing import List

from bench_prelude import Err, Ok, Result


def election_winner(candidates: List[str], ballots: List[str]) -> Result[str]:
    if not candidates:
        return Err("no candidates")
    votes = {name: ballots.count(name) for name in candidates}
    total = sum(votes.values())
    if total == 0:
        return Err("no valid ballots")
    leader = candidates[0]
    for name in candidates[1:]:
        if votes[name] > votes[leader]:
            leader = name
    if votes[leader] * 2 > total:
        return Ok(leader)
    return Err("no majority: %s leads with %d of %d" % (leader, votes[leader], total))
