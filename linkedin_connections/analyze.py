"""Plain, generic analysis over parsed LinkedIn connections.

Four independent views, none tied to any scoring model:

- ``by_year``    - how many connections you added each year (recency shape).
- ``top_companies`` - where your network concentrates.
- ``seniority``  - a rough title-keyword breakdown of seniority.
- ``staleness``  - how much of your network is dormant (old and untouched).

Seniority is a transparent keyword heuristic on the job-title string. It is
deliberately simple and easy to adjust - see ``SENIORITY_KEYWORDS``.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

from .parse import Connection

# Ordered most-senior first: the first bucket whose keywords match wins.
# Keywords are matched on WORD BOUNDARIES (not raw substrings), so "cto" does
# not match inside "director" and "coo" does not match inside "coordinator".
SENIORITY_KEYWORDS: List[Tuple[str, Tuple[str, ...]]] = [
    ("executive", ("chief", "ceo", "cfo", "cto", "coo", "cmo", "cpo", "founder",
                   "president", "partner", "owner")),
    ("vp", ("vp", "vice president", "svp", "evp", "head of")),
    ("director", ("director", "principal")),
    ("manager", ("manager", "lead", "supervisor")),
    ("senior", ("senior", "sr", "staff")),
    ("individual", ("engineer", "developer", "analyst", "associate",
                    "specialist", "coordinator", "consultant", "designer")),
]


def _has_word(text: str, keyword: str) -> bool:
    """True if ``keyword`` appears in ``text`` on word boundaries."""
    return re.search(r"\b" + re.escape(keyword) + r"\b", text) is not None


def classify_seniority(position: str) -> str:
    """Bucket a job title into a seniority level, or ``"unknown"``.

    Uses word-boundary keyword matching. "Vice President" is treated as VP-level
    and is checked before the executive bucket's bare "president" could claim it.
    """
    p = (position or "").lower()
    if not p:
        return "unknown"
    if _has_word(p, "vice president") or _has_word(p, "vp"):
        return "vp"
    for level, keywords in SENIORITY_KEYWORDS:
        if any(_has_word(p, k) for k in keywords):
            return level
    return "unknown"


def by_year(connections: Sequence[Connection]) -> Dict[int, int]:
    """Count connections per year they were made. Undated rows are skipped."""
    counter: Counter = Counter()
    for c in connections:
        if c.connected_year is not None:
            counter[c.connected_year] += 1
    return dict(sorted(counter.items()))


def top_companies(
    connections: Sequence[Connection], limit: int = 20
) -> List[Tuple[str, int]]:
    """Return the ``limit`` most common companies as ``(company, count)`` pairs."""
    counter: Counter = Counter(
        c.company for c in connections if c.company
    )
    return counter.most_common(limit)


def seniority(connections: Sequence[Connection]) -> Dict[str, int]:
    """Return a count of connections in each seniority bucket."""
    counter: Counter = Counter(classify_seniority(c.position) for c in connections)
    # Present buckets in a stable, meaningful order.
    order = [level for level, _ in SENIORITY_KEYWORDS] + ["unknown"]
    return {level: counter.get(level, 0) for level in order if counter.get(level, 0)}


def staleness(
    connections: Sequence[Connection], as_of_year: int, stale_after_years: int = 4
) -> Dict[str, int]:
    """Split the network into active vs. dormant by connection age.

    A connection is ``stale`` if it was made more than ``stale_after_years``
    before ``as_of_year``. Undated connections are counted separately.
    """
    # "More than stale_after_years before as_of_year" means strictly older than
    # the cutoff year: with as_of=2026, stale_after=4, cutoff=2022 and a 2022
    # connection (exactly 4 years) is still active, not stale.
    cutoff = as_of_year - stale_after_years
    active = stale = undated = 0
    for c in connections:
        year = c.connected_year
        if year is None:
            undated += 1
        elif year < cutoff:
            stale += 1
        else:
            active += 1
    return {"active": active, "stale": stale, "undated": undated}


def latest_year(connections: Sequence[Connection]) -> Optional[int]:
    """The most recent connection year in the data, or ``None`` if all undated."""
    years = [c.connected_year for c in connections if c.connected_year is not None]
    return max(years) if years else None


def summary(
    connections: Sequence[Connection],
    *,
    company_limit: int = 20,
    stale_after_years: int = 4,
    as_of_year: Optional[int] = None,
) -> Dict[str, object]:
    """Run every analysis and return a single dict, ready to print or serialize."""
    ref_year = as_of_year or latest_year(connections)
    return {
        "total": len(connections),
        "by_year": by_year(connections),
        "top_companies": top_companies(connections, company_limit),
        "seniority": seniority(connections),
        "staleness": (
            staleness(connections, ref_year, stale_after_years)
            if ref_year is not None
            else {"active": 0, "stale": 0, "undated": len(connections)}
        ),
        "as_of_year": ref_year,
        "stale_after_years": stale_after_years,
    }
