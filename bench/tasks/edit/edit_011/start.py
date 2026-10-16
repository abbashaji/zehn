from __future__ import annotations

from typing import List


def matching_posts(posts: List[str], tags: List[str]) -> List[str]:
    result: List[str] = []
    for post in posts:
        for tag in tags:
            if tag in post:
                result.append(post)
                break
    return result
