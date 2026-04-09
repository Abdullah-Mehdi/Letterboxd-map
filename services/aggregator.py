"""Aggregate films into per-country watch counts.

For each film the original language is checked first.  If that language
maps unambiguously to a single country (e.g. Korean → South Korea,
Japanese → Japan) the film is attributed to that country.  For shared
languages (English, Spanish, French, …) the production countries from
TMDb are used as the fallback.

Alpha-3 codes match the identifiers used in Natural Earth / TopoJSON
world maps.
"""

from collections import defaultdict
from typing import Generator

from services import cache
from services.tmdb import get_details_for_film, search_movie

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
    # Historical / defunct states → modern successor
    "SU": "RUS",  # Soviet Union → Russia
    "DD": "DEU",  # East Germany → Germany
    "XG": "DEU",  # East Germany (TMDb variant) → Germany
    "YU": "SRB",  # Yugoslavia → Serbia
    "CS": "CZE",  # Czechoslovakia / Serbia & Montenegro → Czech Republic
    "XC": "CZE",  # Czechoslovakia (TMDb variant) → Czech Republic
    "BU": "MMR",  # Burma → Myanmar
    "ZR": "COD",  # Zaire → DR Congo
    "TP": "TLS",  # East Timor (old code) → Timor-Leste
    "RH": "ZWE",  # Rhodesia → Zimbabwe
    "DY": "BEN",  # Dahomey → Benin
    "HV": "BFA",  # Upper Volta → Burkina Faso
    "NH": "VUT",  # New Hebrides → Vanuatu
    "VD": "VNM",  # South Vietnam → Vietnam
    "YD": "YEM",  # South Yemen → Yemen
    "XU": "RUS",  # USSR (TMDb variant) → Russia
    "SUHH": "RUS",  # ISO 3166-3 code for USSR → Russia
    "YUCS": "SRB",  # ISO 3166-3 code for Yugoslavia → Serbia
    "CSHH": "CZE",  # ISO 3166-3 code for Czechoslovakia → Czech Republic
    "DDDE": "DEU",  # ISO 3166-3 code for East Germany → Germany
}

ALPHA3_TO_NAME = {v: k for k, v in ALPHA2_TO_ALPHA3.items()}

# ISO 639-1 language code → ISO 3166-1 alpha-2 country code
# Only languages that unambiguously belong to one country.
# Shared languages (en, es, fr, ar, pt, …) are intentionally omitted
# so the aggregator falls back to production_countries for those.
LANG_TO_COUNTRY = {
    # NOTE: Only languages spoken primarily in ONE country belong here.
    # Omitted (fall back to production countries):
    #   ko  - Korean (North Korea + South Korea)
    #   ro  - Romanian (Romania + Moldova)
    #   bn  - Bengali (Bangladesh + India's West Bengal)
    #   sq  - Albanian (Albania + Kosovo)
    #   hi  - Hindi (India + Fiji)
    #   en, es, fr, ar, pt, de, zh, ms, sw, ...  (many countries)
    "ta": "IN",  # Tamil → India
    "te": "IN",  # Telugu → India
    "ja": "JP",  # Japanese → Japan
    "th": "TH",  # Thai → Thailand
    "vi": "VN",  # Vietnamese → Vietnam
    "pl": "PL",  # Polish → Poland
    "cs": "CZ",  # Czech → Czech Republic
    "hu": "HU",  # Hungarian → Hungary
    "el": "GR",  # Greek → Greece
    "he": "IL",  # Hebrew → Israel
    "uk": "UA",  # Ukrainian → Ukraine
    "ka": "GE",  # Georgian → Georgia
    "hy": "AM",  # Armenian → Armenia
    "az": "AZ",  # Azerbaijani → Azerbaijan
    "mn": "MN",  # Mongolian → Mongolia
    "km": "KH",  # Khmer → Cambodia
    "lo": "LA",  # Lao → Laos
    "my": "MM",  # Burmese → Myanmar
    "ne": "NP",  # Nepali → Nepal
    "si": "LK",  # Sinhala → Sri Lanka
    "is": "IS",  # Icelandic → Iceland
    "lv": "LV",  # Latvian → Latvia
    "lt": "LT",  # Lithuanian → Lithuania
    "et": "EE",  # Estonian → Estonia
    "fi": "FI",  # Finnish → Finland
    "da": "DK",  # Danish → Denmark
    "sk": "SK",  # Slovak → Slovakia
    "sl": "SI",  # Slovenian → Slovenia
    "hr": "HR",  # Croatian → Croatia
    "bg": "BG",  # Bulgarian → Bulgaria
    "mk": "MK",  # Macedonian → North Macedonia
    "bs": "BA",  # Bosnian → Bosnia and Herzegovina
    "sr": "RS",  # Serbian → Serbia
    "kk": "KZ",  # Kazakh → Kazakhstan
    "uz": "UZ",  # Uzbek → Uzbekistan
    "tk": "TM",  # Turkmen → Turkmenistan
    "ky": "KG",  # Kyrgyz → Kyrgyzstan
    "tg": "TJ",  # Tajik → Tajikistan
    "tl": "PH",  # Tagalog → Philippines
    "id": "ID",  # Indonesian → Indonesia
    "cn": "CN",  # Cantonese (TMDb uses "cn") → China
    "nb": "NO",  # Norwegian Bokmål → Norway
    "no": "NO",  # Norwegian → Norway
    "sv": "SE",  # Swedish → Sweden
}


# Manual overrides for films that TMDb consistently misattributes.
# Keyed by (title, year) → alpha-3 country code.
TITLE_COUNTRY_OVERRIDE = {
    ("Anuja", 2024): "IND",
    ("Birdsong", 2022): "LAO",
    ("Anima", 2013): "ECU",
    ("Something Old, New, Borrowed and Blue", 2019): "IDN",
    ("Something Old New Borrowed and Blue", 2019): "IDN",
    ("Home", 2018): "GRL",
}


def _extract_slug(letterboxd_uri: str) -> str:
    """Extract the film slug from a Letterboxd URI.

    'https://letterboxd.com/film/paradise-1995/' → 'paradise-1995'
    """
    if not letterboxd_uri:
        return ""
    parts = letterboxd_uri.rstrip("/").split("/")
    return parts[-1] if parts else ""


def _alpha2_to_alpha3(code: str) -> str | None:
    return ALPHA2_TO_ALPHA3.get(code.upper())


def _lang_to_alpha3(lang_code: str) -> str | None:
    """Map an ISO 639-1 language code to an alpha-3 country code,
    but only for unambiguous languages."""
    alpha2 = LANG_TO_COUNTRY.get(lang_code)
    if alpha2 is None:
        return None
    return ALPHA2_TO_ALPHA3.get(alpha2)


def aggregate_countries(
    films: list[dict],
    progress_callback=None,
) -> dict:
    """Build per-country counts and film lists from a film list.

    For each film the original language is checked first. If it maps
    unambiguously to one country the film is attributed there. Otherwise
    the production countries from TMDb are used.

    Args:
        films: list of dicts with keys 'title' and 'year' (from csv_parser).
        progress_callback: optional callable(current, total, title) invoked
                           after each film is processed.

    Returns:
        Dict with keys:
          "counts"      - {alpha3_code: int}
          "films"       - {alpha3_code: ["Title (Year)", ...]}
          "avg_ratings" - {alpha3_code: float}  (only countries with rated films)
    """
    counts: dict[str, int] = defaultdict(int)
    film_lists: dict[str, list[str]] = defaultdict(list)
    rating_sums: dict[str, float] = defaultdict(float)
    rating_counts: dict[str, int] = defaultdict(int)
    total = len(films)

    for i, film in enumerate(films):
        title = film["title"]
        year = film.get("year")
        slug = _extract_slug(film.get("letterboxd_uri", ""))
        rating = film.get("rating")

        cached = cache.get(title, year)
        if cached is not None:
            original_language = cached["original_language"]
            countries = cached["production_countries"]
        else:
            details = get_details_for_film(title, year, slug=slug)
            original_language = details["original_language"]
            countries = details["production_countries"]
            tmdb_id = None
            if countries:
                tmdb_id = search_movie(title, year, slug=slug)
            cache.put(title, year, tmdb_id, countries, original_language)

        label = f"{title} ({year})" if year else title

        def _attribute(alpha3: str) -> None:
            counts[alpha3] += 1
            film_lists[alpha3].append(label)
            if rating is not None:
                rating_sums[alpha3] += rating
                rating_counts[alpha3] += 1

        override = TITLE_COUNTRY_OVERRIDE.get((title, year))
        if override:
            _attribute(override)
        elif (lang_alpha3 := _lang_to_alpha3(original_language)):
            _attribute(lang_alpha3)
        else:
            for c in countries:
                alpha2 = c.get("iso_3166_1", "")
                alpha3 = _alpha2_to_alpha3(alpha2)
                if alpha3:
                    _attribute(alpha3)

        if progress_callback:
            progress_callback(i + 1, total, title)

    avg_ratings = {}
    for code, total_rating in rating_sums.items():
        avg_ratings[code] = round(total_rating / rating_counts[code], 2)

    return {
        "counts": dict(counts),
        "films": dict(film_lists),
        "avg_ratings": avg_ratings,
    }
