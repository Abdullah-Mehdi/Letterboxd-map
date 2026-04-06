"""Parse a Letterboxd CSV export to extract watched films.

The Letterboxd data export ZIP contains a ``watched.csv`` with columns:
    Date, Name, Year, LetterboxdURI

This module handles both the raw ``watched.csv`` file and the full ZIP
archive (automatically locating ``watched.csv`` inside it).
"""

import csv
import io
import zipfile


def parse_watched_csv(file_stream) -> list[dict]:
    """Parse a watched.csv file object and return a list of film dicts.

    Each dict has keys: title, year, letterboxd_uri
    """
    text = file_stream.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text))
    films = []
    for row in reader:
        title = row.get("Name", "").strip()
        if not title:
            continue
        year = row.get("Year", "").strip()
        films.append({
            "title": title,
            "year": int(year) if year.isdigit() else None,
            "letterboxd_uri": row.get("LetterboxdURI", "").strip(),
        })
    return films


def parse_letterboxd_zip(file_stream) -> list[dict]:
    """Extract watched.csv from a Letterboxd export ZIP and parse it."""
    with zipfile.ZipFile(io.BytesIO(file_stream.read())) as zf:
        csv_name = _find_watched_csv(zf)
        if csv_name is None:
            raise ValueError(
                "No watched.csv found in the ZIP. "
                "Make sure you uploaded a Letterboxd data export."
            )
        with zf.open(csv_name) as f:
            return parse_watched_csv(f)


def _find_watched_csv(zf: zipfile.ZipFile) -> str | None:
    """Locate the watched.csv entry inside the ZIP (may be nested)."""
    for name in zf.namelist():
        if name.endswith("watched.csv"):
            return name
    return None
