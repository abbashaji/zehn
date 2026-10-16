interface Span {
  lo: number;
  hi: number;
}

function merge_spans(spans: Span[]): Span[] {
  const merged: Span[] = [];
  for (const s of spans) {
    const last = merged[merged.length - 1];
    if (last !== undefined && s.lo <= last.hi) {
      last.hi = Math.max(last.hi, s.hi);
    } else {
      merged.push({ lo: s.lo, hi: s.hi });
    }
  }
  return merged;
}
