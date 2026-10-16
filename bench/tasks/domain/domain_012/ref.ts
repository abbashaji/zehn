type Result<T> = { ok: true; value: T } | { ok: false; error: string };

interface Tally {
  name: string;
  votes: number;
}

function election_winner(candidates: string[], ballots: string[]): Result<string> {
  const tally: Tally[] = candidates.map((name) => ({
    name,
    votes: ballots.filter((b) => b === name).length,
  }));
  const [first, ...others] = tally;
  if (first === undefined) {
    return { ok: false, error: "no candidates" };
  }
  const total = tally.reduce((sum, t) => sum + t.votes, 0);
  if (total === 0) {
    return { ok: false, error: "no valid ballots" };
  }
  let leader = first;
  for (const t of others) {
    if (t.votes > leader.votes) {
      leader = t;
    }
  }
  if (leader.votes * 2 > total) {
    return { ok: true, value: leader.name };
  }
  return {
    ok: false,
    error: "no majority: " + leader.name + " leads with " + leader.votes + " of " + total,
  };
}
