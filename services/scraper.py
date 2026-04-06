"""Scrape a Letterboxd user's watched films from their public profile.

Parses the paginated /username/films/ pages to extract film titles and
slugs.  Output format matches csv_parser: list of {title, year,
letterboxd_uri} dicts.

Uses cloudscraper to handle Cloudflare's JS challenge on letterboxd.com.
"""

import re
import concurrent.futures

import cloudscraper
from bs4 import BeautifulSoup

LETTERBOXD_BASE = "https://letterboxd.com"
_scraper = cloudscraper.create_scraper()

_YEAR_FROM_NAME = re.compile(r"^(.+?)\s*\((\d{4})\)$")


def _get_soup(url: str) -> BeautifulSoup:
    resp = _scraper.get(url, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def _get_page_count(username: str) -> int:
    """Determine how many pages of films a user has (72 films/page)."""
    soup = _get_soup(f"{LETTERBOXD_BASE}/{username}/films/")
    pages = soup.select("li.paginate-page a")
    if not pages:
        return 1
    return int(pages[-1].text.strip())


def _scrape_page(url: str) -> list[dict]:
    """Extract films from a single /films/page/N listing page.

    Each film's data lives on div.react-component[data-component-class=LazyPoster]
    with attributes: data-item-name ("Title (Year)"), data-item-slug,
    data-target-link.
    """
    soup = _get_soup(url)
    films = []
    for wrapper in soup.select('div[data-component-class="LazyPoster"]'):
        item_name = wrapper.get("data-item-name", "")
        target = wrapper.get("data-target-link", "")

        title, year = _parse_item_name(item_name)
        if not title:
            continue

        films.append({
            "title": title,
            "year": year,
            "letterboxd_uri": f"{LETTERBOXD_BASE}{target}" if target else "",
        })
    return films


def _parse_item_name(name: str) -> tuple[str, int | None]:
    """Parse 'Title (YYYY)' into (title, year). Falls back to (name, None)."""
    m = _YEAR_FROM_NAME.match(name)
    if m:
        return m.group(1).strip(), int(m.group(2))
    return name.strip(), None


def scrape_user_films(username: str) -> list[dict]:
    """Scrape all watched films for a Letterboxd user.

    Returns a list of dicts matching the csv_parser output format:
        [{"title": str, "year": int|None, "letterboxd_uri": str}, ...]

    Raises:
        requests.HTTPError: if the user profile is not accessible (404, etc.)
    """
    page_count = _get_page_count(username)
    base = f"{LETTERBOXD_BASE}/{username}/films/page/"
    urls = [f"{base}{i}" for i in range(1, page_count + 1)]

    all_films = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(_scrape_page, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_map):
            all_films.extend(future.result())

    return all_films
