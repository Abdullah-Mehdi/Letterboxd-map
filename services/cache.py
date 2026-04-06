"""SQLite cache for TMDb lookup results.

Keyed by (title, year) so the same film is never looked up twice across
sessions.  The cache stores the raw production_countries JSON from TMDb.
"""

import json
import sqlite3

from config import CACHE_DB_PATH

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS tmdb_cache (
    title TEXT NOT NULL,
    year  INTEGER,
    tmdb_id INTEGER,
    countries TEXT NOT NULL,
    PRIMARY KEY (title, year)
)
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


def get(title: str, year: int | None) -> list[dict] | None:
    """Return cached production countries, or None on cache miss."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT countries FROM tmdb_cache WHERE title = ? AND year IS ?",
            (title, year),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])
    finally:
        conn.close()


def put(title: str, year: int | None, tmdb_id: int | None,
        countries: list[dict]) -> None:
    """Store production countries in the cache."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO tmdb_cache (title, year, tmdb_id, countries) "
            "VALUES (?, ?, ?, ?)",
            (title, year, tmdb_id, json.dumps(countries)),
        )
        conn.commit()
    finally:
        conn.close()


def clear() -> None:
    """Delete all cached entries."""
    conn = _connect()
    try:
        conn.execute("DELETE FROM tmdb_cache")
        conn.commit()
    finally:
        conn.close()
