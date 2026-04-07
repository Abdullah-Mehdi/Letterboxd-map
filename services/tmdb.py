"""TMDb API client for looking up film metadata.

Two-step process:
    1. Search for a film by title (+year) to get its TMDb ID.
    2. Fetch movie details by TMDb ID to get original_language and
       production_countries.
"""

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


def search_movie(title: str, year: int | None = None) -> int | None:
    """Search TMDb for a movie by title and optional year.

    Returns the TMDb movie ID of the best match, or None if not found.
    """
    params = {"query": title}
    if year:
        params["year"] = year
    data = _get("/search/movie", params)
    results = data.get("results", [])
    if not results:
        return None
    return results[0]["id"]


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


def get_details_for_film(title: str, year: int | None = None) -> dict:
    """Convenience: search + fetch details in one call.

    Returns a dict with original_language and production_countries,
    or defaults if the film wasn't found on TMDb.
    """
    movie_id = search_movie(title, year)
    if movie_id is None:
        return {"original_language": "", "production_countries": []}
    return get_movie_details(movie_id)
