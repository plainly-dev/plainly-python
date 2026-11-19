"""Collects every check as a plain-English sentence so reviewers can read the spec."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Record:
    sentence: str
    passed: bool
    prose: str = ""  # why this wording was typed by the author instead of derived from the code, if so
    where: str = ""  # what to review: the adapter's location, the template, or the label itself


_records: List[Record] = []


def add(sentence: str, passed: bool, prose: str = "", where: str = "") -> None:
    _records.append(Record(sentence, passed, prose, where))


def drain() -> List[Record]:
    """Return and clear everything recorded so far."""
    taken = list(_records)
    _records.clear()
    return taken
