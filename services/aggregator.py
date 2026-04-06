"""Aggregate film production countries into per-country watch counts.

Takes a list of films (from the CSV parser), resolves each
film's production countries via TMDb (with cache), and returns a dict
mapping ISO 3166-1 alpha-3 country codes to watch counts.  Alpha-3 codes
match the identifiers used in Natural Earth / TopoJSON world maps.
"""

from collections import defaultdict
from typing import Generator

from services import cache
from services.tmdb import get_countries_for_film, search_movie

# ISO 3166-1 alpha-2 → alpha-3 mapping (all current countries)
ALPHA2_TO_ALPHA3 = {
    "AF": "AFG", "AL": "ALB", "DZ": "DZA", "AS": "ASM", "AD": "AND",
    "AO": "AGO", "AG": "ATG", "AR": "ARG", "AM": "ARM", "AU": "AUS",
    "AT": "AUT", "AZ": "AZE", "BS": "BHS", "BH": "BHR", "BD": "BGD",
    "BB": "BRB", "BY": "BLR", "BE": "BEL", "BZ": "BLZ", "BJ": "BEN",
    "BT": "BTN", "BO": "BOL", "BA": "BIH", "BW": "BWA", "BR": "BRA",
    "BN": "BRN", "BG": "BGR", "BF": "BFA", "BI": "BDI", "CV": "CPV",
    "KH": "KHM", "CM": "CMR", "CA": "CAN", "CF": "CAF", "TD": "TCD",
    "CL": "CHL", "CN": "CHN", "CO": "COL", "KM": "COM", "CG": "COG",
    "CD": "COD", "CR": "CRI", "CI": "CIV", "HR": "HRV", "CU": "CUB",
    "CY": "CYP", "CZ": "CZE", "DK": "DNK", "DJ": "DJI", "DM": "DMA",
    "DO": "DOM", "EC": "ECU", "EG": "EGY", "SV": "SLV", "GQ": "GNQ",
    "ER": "ERI", "EE": "EST", "SZ": "SWZ", "ET": "ETH", "FJ": "FJI",
    "FI": "FIN", "FR": "FRA", "GA": "GAB", "GM": "GMB", "GE": "GEO",
    "DE": "DEU", "GH": "GHA", "GR": "GRC", "GD": "GRD", "GT": "GTM",
    "GN": "GIN", "GW": "GNB", "GY": "GUY", "HT": "HTI", "HN": "HND",
    "HU": "HUN", "IS": "ISL", "IN": "IND", "ID": "IDN", "IR": "IRN",
    "IQ": "IRQ", "IE": "IRL", "IL": "ISR", "IT": "ITA", "JM": "JAM",
    "JP": "JPN", "JO": "JOR", "KZ": "KAZ", "KE": "KEN", "KI": "KIR",
    "KP": "PRK", "KR": "KOR", "KW": "KWT", "KG": "KGZ", "LA": "LAO",
    "LV": "LVA", "LB": "LBN", "LS": "LSO", "LR": "LBR", "LY": "LBY",
    "LI": "LIE", "LT": "LTU", "LU": "LUX", "MG": "MDG", "MW": "MWI",
    "MY": "MYS", "MV": "MDV", "ML": "MLI", "MT": "MLT", "MH": "MHL",
    "MR": "MRT", "MU": "MUS", "MX": "MEX", "FM": "FSM", "MD": "MDA",
    "MC": "MCO", "MN": "MNG", "ME": "MNE", "MA": "MAR", "MZ": "MOZ",
    "MM": "MMR", "NA": "NAM", "NR": "NRU", "NP": "NPL", "NL": "NLD",
    "NZ": "NZL", "NI": "NIC", "NE": "NER", "NG": "NGA", "MK": "MKD",
    "NO": "NOR", "OM": "OMN", "PK": "PAK", "PW": "PLW", "PS": "PSE",
    "PA": "PAN", "PG": "PNG", "PY": "PRY", "PE": "PER", "PH": "PHL",
    "PL": "POL", "PT": "PRT", "QA": "QAT", "RO": "ROU", "RU": "RUS",
    "RW": "RWA", "KN": "KNA", "LC": "LCA", "VC": "VCT", "WS": "WSM",
    "SM": "SMR", "ST": "STP", "SA": "SAU", "SN": "SEN", "RS": "SRB",
    "SC": "SYC", "SL": "SLE", "SG": "SGP", "SK": "SVK", "SI": "SVN",
    "SB": "SLB", "SO": "SOM", "ZA": "ZAF", "SS": "SSD", "ES": "ESP",
    "LK": "LKA", "SD": "SDN", "SR": "SUR", "SE": "SWE", "CH": "CHE",
    "SY": "SYR", "TW": "TWN", "TJ": "TJK", "TZ": "TZA", "TH": "THA",
    "TL": "TLS", "TG": "TGO", "TO": "TON", "TT": "TTO", "TN": "TUN",
    "TR": "TUR", "TM": "TKM", "TV": "TUV", "UG": "UGA", "UA": "UKR",
    "AE": "ARE", "GB": "GBR", "US": "USA", "UY": "URY", "UZ": "UZB",
    "VU": "VUT", "VE": "VEN", "VN": "VNM", "YE": "YEM", "ZM": "ZMB",
    "ZW": "ZWE", "XK": "XKX", "HK": "HKG", "MO": "MAC", "PR": "PRI",
    "GF": "GUF", "GP": "GLP", "MQ": "MTQ", "RE": "REU", "YT": "MYT",
    "NC": "NCL", "PF": "PYF", "AW": "ABW", "CW": "CUW", "SX": "SXM",
    "AN": "ANT",
}

ALPHA3_TO_NAME = {v: k for k, v in ALPHA2_TO_ALPHA3.items()}


def _alpha2_to_alpha3(code: str) -> str | None:
    return ALPHA2_TO_ALPHA3.get(code.upper())


def aggregate_countries(
    films: list[dict],
    progress_callback=None,
) -> dict:
    """Build per-country counts and film lists from a film list.

    Args:
        films: list of dicts with keys 'title' and 'year' (from csv_parser).
        progress_callback: optional callable(current, total, title) invoked
                           after each film is processed.

    Returns:
        Dict with two keys:
          "counts" - {alpha3_code: int}
          "films"  - {alpha3_code: ["Title (Year)", ...]}
    """
    counts: dict[str, int] = defaultdict(int)
    film_lists: dict[str, list[str]] = defaultdict(list)
    total = len(films)

    for i, film in enumerate(films):
        title = film["title"]
        year = film.get("year")

        cached = cache.get(title, year)
        if cached is not None:
            countries = cached
        else:
            countries = get_countries_for_film(title, year)
            tmdb_id = None
            if countries:
                tmdb_id = search_movie(title, year)
            cache.put(title, year, tmdb_id, countries)

        label = f"{title} ({year})" if year else title

        for c in countries:
            alpha2 = c.get("iso_3166_1", "")
            alpha3 = _alpha2_to_alpha3(alpha2)
            if alpha3:
                counts[alpha3] += 1
                film_lists[alpha3].append(label)

        if progress_callback:
            progress_callback(i + 1, total, title)

    return {
        "counts": dict(counts),
        "films": dict(film_lists),
    }
