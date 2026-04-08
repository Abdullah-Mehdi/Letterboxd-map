"""Parse a Letterboxd CSV export to extract watched films and ratings.

The Letterboxd data export ZIP contains:
    ``watched.csv``  – Date, Name, Year, LetterboxdURI
    ``ratings.csv``  – Date, Name, Year, LetterboxdURI, Rating

This module handles both the raw CSV files and the full ZIP archive.
"""

import csv
import io
import zipfile


def parse_watched_csv(file_stream) -> list[dict]:
    """Parse a watched.csv file object and return a list of film dicts.

    Each dict has keys: title, year, letterboxd_uri, rating (always None
    when parsed from watched.csv alone).
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
            "rating": None,
        })
    return films


def _parse_ratings_csv(file_stream) -> dict[tuple[str, int | None], float]:
    """Parse ratings.csv and return a lookup of (title, year) → rating."""
    text = file_stream.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text))
    ratings: dict[tuple[str, int | None], float] = {}
    for row in reader:
        title = row.get("Name", "").strip()
        if not title:
            continue
        year_str = row.get("Year", "").strip()
        year = int(year_str) if year_str.isdigit() else None
        rating_str = row.get("Rating", "").strip()
        if rating_str:
            try:
                ratings[(title, year)] = float(rating_str)
            except ValueError:
                pass
    return ratings


def parse_letterboxd_zip(file_stream) -> list[dict]:
    """Extract watched.csv (and optionally ratings.csv) from a ZIP."""
    with zipfile.ZipFile(io.BytesIO(file_stream.read())) as zf:
        watched_name = _find_csv(zf, "watched.csv")
        if watched_name is None:
            raise ValueError(
                "No watched.csv found in the ZIP. "
                "Make sure you uploaded a Letterboxd data export."
            )
        with zf.open(watched_name) as f:
            films = parse_watched_csv(f)

        ratings_name = _find_csv(zf, "ratings.csv")
        if ratings_name is not None:
            with zf.open(ratings_name) as f:
                ratings = _parse_ratings_csv(f)
            for film in films:
                key = (film["title"], film["year"])
                if key in ratings:
                    film["rating"] = ratings[key]

        return films


def _find_csv(zf: zipfile.ZipFile, filename: str) -> str | None:
    """Locate a CSV entry inside the ZIP (may be nested in a folder)."""
    for name in zf.namelist():
        if name.endswith(filename):
            return name
    return None
