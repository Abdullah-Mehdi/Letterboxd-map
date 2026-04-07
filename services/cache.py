"""SQLite cache for TMDb lookup results.

Keyed by (title, year) so the same film is never looked up twice across
sessions.  The cache stores original_language and the raw
production_countries JSON from TMDb.
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
    original_language TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (title, year)
)
"""

_MIGRATE_LANG_COLUMN = (
    "ALTER TABLE tmdb_cache ADD COLUMN original_language TEXT NOT NULL DEFAULT ''"
)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.execute(_CREATE_TABLE)
    # Add the column for databases created before this migration
    try:
        conn.execute(_MIGRATE_LANG_COLUMN)
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()
    return conn


def get(title: str, year: int | None) -> dict | None:
    """Return cached film details, or None on cache miss.

    Returns a dict with keys: original_language, production_countries.
    """
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT countries, original_language FROM tmdb_cache "
            "WHERE title = ? AND year IS ?",
            (title, year),
        ).fetchone()
        if row is None:
            return None
        return {
            "production_countries": json.loads(row[0]),
            "original_language": row[1] or "",
        }
    finally:
        conn.close()


def put(title: str, year: int | None, tmdb_id: int | None,
        countries: list[dict], original_language: str = "") -> None:
    """Store film details in the cache."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO tmdb_cache "
            "(title, year, tmdb_id, countries, original_language) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, year, tmdb_id, json.dumps(countries), original_language),
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
