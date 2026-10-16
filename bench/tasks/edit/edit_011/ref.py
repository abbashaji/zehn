from __future__ import annotations

from typing import List


def matching_posts(posts: List[str], tags: List[str]) -> List[str]:
    wanted = [t.upper() for t in tags]
    return [p for p in posts if all(t in p.upper() for t in wanted)]
