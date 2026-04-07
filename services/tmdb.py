"""TMDb API client for looking up film metadata.

Two-step process:
    1. Search for a film by title (+year) to get its TMDb ID.
       When a Letterboxd slug is available it is used to disambiguate
       among multiple search results with the same title.
    2. Fetch movie details by TMDb ID to get original_language and
       production_countries.
"""

import re
import time

import requests

from config import TMDB_API_KEY, TMDB_BASE_URL

_session = requests.Session()

RATE_LIMIT_DELAY = 0.26  # ~4 requests/sec keeps us well under TMDb's 40/10s


MAX_RETRIES = 3


def _get(endpoint: str, params: dict | None = None) -> dict:
    """Make a GET request to the TMDb API with rate limiting and retries."""
    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is not set. "
            "Export it as an environment variable before running."
        )
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    url = f"{TMDB_BASE_URL}{endpoint}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = _session.get(url, params=params, timeout=10)
        except requests.RequestException:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
            continue

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 2))
            time.sleep(retry_after)
            continue

        resp.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY)
        return resp.json()

    resp.raise_for_status()
    return resp.json()


def _normalize(text: str) -> str:
    """Lowercase, strip non-alphanumeric, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _slug_to_words(slug: str) -> str:
    """Convert a Letterboxd slug like 'paradise-1995' to 'paradise 1995'."""
    return slug.replace("-", " ").strip()


def _score_result(result: dict, title: str, year: int | None,
                  slug_words: str) -> float:
    """Score a TMDb search result for how well it matches our film."""
    score = 0.0

    title_norm = _normalize(title)
    tmdb_title = _normalize(result.get("title", ""))
    tmdb_original = _normalize(result.get("original_title", ""))

    if tmdb_title == title_norm:
        score += 5
    if tmdb_original == title_norm:
        score += 3

    release_date = result.get("release_date", "") or ""
    if year and release_date.startswith(str(year)):
        score += 4

    if slug_words:
        slug_norm = _normalize(slug_words)
        for t in (tmdb_title, tmdb_original):
            if t == slug_norm:
                score += 6
            elif t and (t in slug_norm or slug_norm in t):
                score += 2

    return score


def search_movie(title: str, year: int | None = None,
                 slug: str = "") -> int | None:
    """Search TMDb for a movie by title and optional year.

    When *slug* (the Letterboxd URI slug) is provided and there are
    multiple results, scores each result to pick the best match rather
    than blindly returning the first.
    """
    params = {"query": title}
    if year:
        params["year"] = year
    data = _get("/search/movie", params)
    results = data.get("results", [])
    if not results:
        return None
    if len(results) == 1:
        return results[0]["id"]

    slug_words = _slug_to_words(slug) if slug else ""
    best_id = results[0]["id"]
    best_score = _score_result(results[0], title, year, slug_words)

    for r in results[1:]:
        s = _score_result(r, title, year, slug_words)
        if s > best_score:
            best_score = s
            best_id = r["id"]

    return best_id


def get_movie_details(movie_id: int) -> dict:
    """Fetch original_language and production_countries for a TMDb movie ID.

    Returns a dict with keys:
        original_language: ISO 639-1 code (e.g. "ko")
        production_countries: list of dicts with iso_3166_1 and name
    """
    data = _get(f"/movie/{movie_id}")
    return {
        "original_language": data.get("original_language", ""),
        "production_countries": data.get("production_countries", []),
    }


def get_details_for_film(title: str, year: int | None = None,
                         slug: str = "") -> dict:
    """Convenience: search + fetch details in one call.

    Returns a dict with original_language and production_countries,
    or defaults if the film wasn't found on TMDb.
    """
    movie_id = search_movie(title, year, slug=slug)
    if movie_id is None:
        return {"original_language": "", "production_countries": []}
    return get_movie_details(movie_id)
