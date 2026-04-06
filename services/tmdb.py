"""TMDb API client for looking up film production countries.

Two-step process:
    1. Search for a film by title (+year) to get its TMDb ID.
    2. Fetch movie details by TMDb ID to get production_countries.
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


def get_production_countries(movie_id: int) -> list[dict]:
    """Fetch production countries for a TMDb movie ID.

    Returns a list of dicts with keys: iso_3166_1 (alpha-2 code), name.
    Example: [{"iso_3166_1": "KR", "name": "South Korea"}]
    """
    data = _get(f"/movie/{movie_id}")
    return data.get("production_countries", [])


def get_countries_for_film(title: str, year: int | None = None) -> list[dict]:
    """Convenience: search + fetch countries in one call.

    Returns the production_countries list, or an empty list if the film
    wasn't found on TMDb.
    """
    movie_id = search_movie(title, year)
    if movie_id is None:
        return []
    return get_production_countries(movie_id)
