import os

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")
