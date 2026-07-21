"""A small, dependency-free toolkit for parsing and analyzing a LinkedIn
``Connections.csv`` export.

Public API:

    from linkedin_connections import load_connections, Connection, summary

Everything is stdlib-only and works offline on data you already own.
"""

from __future__ import annotations

from .analyze import (
    by_year,
    classify_seniority,
    seniority,
    staleness,
    summary,
    top_companies,
)
from .parse import Connection, load_connections, iter_connections, parse_connected_on

__all__ = [
    "Connection",
    "load_connections",
    "iter_connections",
    "parse_connected_on",
    "by_year",
    "top_companies",
    "seniority",
    "classify_seniority",
    "staleness",
    "summary",
]

__version__ = "0.1.0"
