"""Parse a LinkedIn ``Connections.csv`` export into normalized records.

LinkedIn's export prepends a few human-readable "Notes:" lines before the real
CSV header row (the one containing ``First Name``). This module skips that
preamble, reads the columns that are stable across export versions, and parses
the ``Connected On`` date into a real ``datetime.date``.

Nothing here is specific to any scoring system - it is a plain, reusable ETL
layer you can build your own analysis on top of.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterator, List, Optional

# Column headers LinkedIn uses. Kept here so a future export rename is a
# one-line change, not a hunt through the code.
COL_FIRST = "First Name"
COL_LAST = "Last Name"
COL_URL = "URL"
COL_EMAIL = "Email Address"
COL_COMPANY = "Company"
COL_POSITION = "Position"
COL_CONNECTED = "Connected On"

# Date formats seen across LinkedIn export versions, tried in order.
_DATE_FORMATS = ("%d %b %Y", "%d %B %Y", "%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d")


@dataclass(frozen=True)
class Connection:
    """One connection, normalized. Fields absent in the export are ``""``/``None``."""

    first_name: str
    last_name: str
    company: str
    position: str
    url: str
    email: str
    connected_on: Optional[date]

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def connected_year(self) -> Optional[int]:
        return self.connected_on.year if self.connected_on else None


def parse_connected_on(value: str) -> Optional[date]:
    """Parse a ``Connected On`` cell into a ``date``, or ``None`` if unparseable."""
    value = (value or "").strip()
    if not value:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _find_header_index(lines: List[str]) -> int:
    """Return the index of the real header row (the one naming the columns).

    LinkedIn puts a "Notes:" preamble before it. We anchor on ``First Name``,
    which has been present in every export version.
    """
    for i, line in enumerate(lines):
        if COL_FIRST in line:
            return i
    raise ValueError(
        f"Could not find a header row containing {COL_FIRST!r}. "
        "Is this a LinkedIn Connections.csv export?"
    )


def iter_connections(path: str) -> Iterator[Connection]:
    """Yield ``Connection`` records from a Connections.csv export at ``path``."""
    # utf-8-sig transparently strips the BOM LinkedIn writes.
    with open(path, newline="", encoding="utf-8-sig") as f:
        lines = f.readlines()

    start = _find_header_index(lines)
    reader = csv.DictReader(lines[start:])
    for row in reader:
        yield Connection(
            first_name=(row.get(COL_FIRST) or "").strip(),
            last_name=(row.get(COL_LAST) or "").strip(),
            company=(row.get(COL_COMPANY) or "").strip(),
            position=(row.get(COL_POSITION) or "").strip(),
            url=(row.get(COL_URL) or "").strip(),
            email=(row.get(COL_EMAIL) or "").strip(),
            connected_on=parse_connected_on(row.get(COL_CONNECTED) or ""),
        )


def load_connections(path: str) -> List[Connection]:
    """Load all connections from a Connections.csv export at ``path``."""
    return list(iter_connections(path))
