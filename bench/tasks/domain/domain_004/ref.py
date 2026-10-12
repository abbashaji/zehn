from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bench_prelude import Err, Ok, Result


@dataclass
class Student:
    name: str
    score: int


@dataclass
class Graded:
    name: str
    grade: str


def _letter(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def assign_grades(students: List[Student], curve: int) -> Result[List[Graded]]:
    if curve < 0:
        return Err("curve must not be negative")
    graded: List[Graded] = []
    for s in students:
        if s.score < 0 or s.score > 100:
            return Err("invalid score for " + s.name)
        graded.append(Graded(s.name, _letter(min(100, s.score + curve))))
    return Ok(graded)
